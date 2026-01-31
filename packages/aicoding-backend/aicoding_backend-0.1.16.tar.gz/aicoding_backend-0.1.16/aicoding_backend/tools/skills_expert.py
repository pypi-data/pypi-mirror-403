"""
Skills 智能技能工具
根据用户需求描述或需求文件，自动匹配并执行相应的技能来完成任务

"""

import re
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from ..utils.file_utils import file_exists, dir_exists, write_file, read_dir
from ..utils.file_reader import read_file


class SkillMetadata(BaseModel):
    """技能元数据类型"""
    name: str  # 显示名称（可能包含中文）
    description: str
    dir_name: str  # 目录名称（用于构建路径）
    location: str = "project"


class SkillsExpertParam(BaseModel):
    """skills_expert 工具的参数结构"""
    requirements: Optional[str] = Field(
        None,
        description="用户需求描述"
    )
    requirements_file: Optional[str] = Field(
        None,
        description="需求文件相对项目根目录的路径"
    )
    repo_path: str = Field(
        ...,
        description="Git 仓库目录（绝对路径）"
    )


def get_skill_summary_path(repo_path: str) -> Path:
    """
    获取汇总文件路径
    
    Args:
        repo_path: 项目根目录路径
        
    Returns:
        汇总文件的完整路径
    """
    return Path(repo_path) / '.joycode' / 'skills' / 'SKILL.md'


async def read_skill_summary(repo_path: str) -> Optional[List[SkillMetadata]]:
    """
    读取汇总文件内容，解析为技能列表
    
    Args:
        repo_path: 项目根目录路径
        
    Returns:
        技能元数据列表，文件不存在时返回 None
    """
    try:
        summary_path = get_skill_summary_path(repo_path)
        
        if not file_exists(summary_path):
            return None
        
        content = await read_file(summary_path)
        skills = parse_skill_summary_content(content)
        return skills
    except Exception:
        return None


def parse_skill_summary_content(content: str) -> List[SkillMetadata]:
    """
    解析汇总文件内容为技能列表
    
    Args:
        content: 汇总文件内容
        
    Returns:
        技能元数据列表
    """
    skills: List[SkillMetadata] = []
    
    try:
        # 匹配所有三级标题（### skill-name）和其后的描述
        # 格式：### name|dir_name\n描述
        skill_pattern = r'###\s+(.+?)\n([\s\S]*?)(?=\n###|$)'
        matches = re.finditer(skill_pattern, content)
        
        for match in matches:
            title = match.group(1).strip()
            description = match.group(2).strip()
            
            if title:
                # 检查是否包含目录名（格式：name|dir_name）
                if '|' in title:
                    name, dir_name = title.split('|', 1)
                    name = name.strip()
                    dir_name = dir_name.strip()
                else:
                    # 兼容旧格式：如果没有目录名，使用名称作为目录名（需要转换为小写和连字符）
                    name = title
                    # 尝试将中文名称转换为目录名格式
                    dir_name = name.lower().replace(' ', '-').replace('_', '-')
                    # 移除特殊字符，只保留字母、数字和连字符
                    dir_name = re.sub(r'[^a-z0-9-]', '', dir_name)
                
                skills.append(SkillMetadata(
                    name=name,
                    description=description or '暂无描述',
                    dir_name=dir_name,
                    location='project'
                ))
    except Exception:
        # ignore
        pass
    
    return skills


def generate_skill_summary_content(skills: List[SkillMetadata]) -> str:
    """
    生成汇总文件的 Markdown 内容
    
    Args:
        skills: 技能元数据列表
        
    Returns:
        格式化的 Markdown 内容
    """
    content = """# Skills 汇总

本文件作为技能索引，记录项目中所有可用的技能，由系统自动维护。
通过索引机制实现技能的快速定位和高效执行。

## 技能列表

"""
    
    for skill in skills:
        # 格式：### name|dir_name\n描述
        # 这样可以在解析时同时获取显示名和目录名
        content += f"### {skill.name}|{skill.dir_name}\n{skill.description}\n\n"
    
    return content


async def write_skill_summary(repo_path: str, skills: List[SkillMetadata]) -> None:
    """
    将技能列表写入汇总文件
    
    Args:
        repo_path: 项目根目录路径
        skills: 技能元数据列表
    """
    try:
        summary_path = get_skill_summary_path(repo_path)
        content = generate_skill_summary_content(skills)
        
        write_file(summary_path, content)
    except Exception:
        # ignore
        pass


def parse_skill_metadata(content: str, skill_dir_name: str) -> Optional[SkillMetadata]:
    """
    解析SKILL.md文件，提取技能元数据
    
    Args:
        content: SKILL.md文件内容
        skill_dir_name: 技能目录名称（用于构建路径）
        
    Returns:
        技能元数据，如果解析失败返回None
    """
    try:
        # 提取name字段（优先使用YAML前置matter中的name）
        name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else skill_dir_name
        
        # 提取description字段（优先使用YAML前置matter中的description）
        desc_match = re.search(r'^description:\s*(.+)$', content, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else ''
        
        # 如果没有在YAML中找到description，尝试从内容中提取第一个段落
        if not description:
            first_paragraph_match = re.search(r'^# .+?\n\n(.+?)(?:\n\n|$)', content, re.DOTALL)
            description = first_paragraph_match.group(1).strip() if first_paragraph_match else '暂无描述'
        
        return SkillMetadata(
            name=name,
            description=description,
            dir_name=skill_dir_name,  # 保存实际的目录名
            location='project'
        )
    except Exception:
        return None


async def scan_skills_directory(repo_path: str) -> List[SkillMetadata]:
    """
    扫描 skills 目录获取所有技能
    
    Args:
        repo_path: 项目根目录路径
        
    Returns:
        技能元数据列表
    """
    try:
        skills_dir = Path(repo_path) / '.joycode' / 'skills'
        
        if not dir_exists(skills_dir):
            return []
        
        skill_dirs = read_dir(skills_dir)
        skills: List[SkillMetadata] = []
        
        for skill_dir_name in skill_dirs:
            # 跳过汇总文件和隐藏文件
            if skill_dir_name == 'SKILL.md' or skill_dir_name.startswith('.'):
                continue
            
            skill_path = skills_dir / skill_dir_name / 'SKILL.md'
            
            if file_exists(skill_path):
                try:
                    skill_content = await read_file(skill_path)
                    skill_info = parse_skill_metadata(skill_content, skill_dir_name)
                    
                    if skill_info:
                        skills.append(skill_info)
                except Exception:
                    # ignore
                    pass
        
        return skills
    except Exception:
        return []


async def append_skill_to_summary(repo_path: str, new_skill: SkillMetadata) -> None:
    """
    将新发现的技能追加到汇总文件
    
    Args:
        repo_path: 项目根目录路径
        new_skill: 新技能的元数据
    """
    try:
        # 读取现有汇总文件
        existing_skills = await read_skill_summary(repo_path)
        
        if not existing_skills:
            existing_skills = []
        
        # 检查技能是否已存在
        exists = any(skill.name == new_skill.name for skill in existing_skills)
        
        if exists:
            return
        
        # 追加新技能
        existing_skills.append(new_skill)
        
        # 写回汇总文件
        await write_skill_summary(repo_path, existing_skills)
    except Exception:
        # ignore
        pass


async def get_available_skills(repo_path: str) -> List[SkillMetadata]:
    """
    获取指定目录下的所有skills
    采用索引机制优化性能：优先从汇总文件读取，避免全目录扫描
    
    Args:
        repo_path: 项目根目录路径
        
    Returns:
        技能元数据列表
    """
    try:
        # 步骤1: 检查汇总文件是否存在
        summary_skills = await read_skill_summary(repo_path)
        
        # 步骤2: 获取物理目录下的技能列表，用于同步检查
        skills_dir = Path(repo_path) / '.joycode' / 'skills'
        skill_dirs: List[str] = []
        if dir_exists(skills_dir):
            entries = read_dir(skills_dir)
            skill_dirs = [d for d in entries if d != 'SKILL.md' and not d.startswith('.')]
        
        if summary_skills and len(summary_skills) > 0:
            # 检查汇总文件是否与实际目录同步（简单的数量对比，如果目录中有新技能则触发重扫）
            if len(skill_dirs) == len(summary_skills):
                return summary_skills
        
        # 步骤3: 汇总文件不存在、为空或不同步，执行目录扫描
        scanned_skills = await scan_skills_directory(repo_path)
        
        if len(scanned_skills) == 0:
            return []
        
        # 步骤4: 扫描后生成汇总文件
        try:
            await write_skill_summary(repo_path, scanned_skills)
        except Exception:
            # ignore
            pass
        
        return scanned_skills
    except Exception:
        return []


async def match_and_execute_skill(
    requirements: str,
    repo_path: str,
    file_path: Optional[str] = None
) -> str:
    """
    匹配并执行skills
    
    Args:
        requirements: 用户需求内容
        repo_path: 项目根目录路径
        file_path: 关联文件路径（可选）
        
    Returns:
        执行指导提示
    """
    try:
        # 获取所有skills，目录为repoPath/.joycode/skills/
        # 优先从汇总文件快速获取技能索引
        available_skills = await get_available_skills(repo_path)
        
        if len(available_skills) == 0:
            return f"""未找到可用的skills，请确保项目目录下存在 .joycode/skills 目录和相应的skills文件。

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir={repo_path}, tool_type=skills_expert"""
        
        # 构建详细的skills列表，包含目录名信息（用于大模型匹配和路径构建）
        skills_list_with_dir = '\n'.join([
            f"- {skill.name} (目录: {skill.dir_name}): {skill.description}"
            for skill in available_skills
        ])
        
        # 生成指导大模型匹配和执行skills的提示
        skill_execution_prompt = f"""# Skill 匹配与执行指导

## 索引机制说明

本系统采用汇总文件索引机制，实现技能的快速定位和高效执行：

1. **索引查找**：下面的技能列表来自系统索引，包含所有可用技能的 name 和 description
2. **智能匹配**：根据用户需求，从索引中快速识别最匹配的技能
3. **快速定位**：使用标准路径 `{repo_path}/.joycode/skills/{{skill.dir_name}}/SKILL.md` 直接读取技能详情
4. **高效执行**：避免全目录扫描，实现"索引查找 → 快速定位 → 高效执行"的流程

**重要提示**：技能名称（name）可能包含中文，但构建路径时必须使用目录名（dir_name）！

## 用户需求
{requirements}

## 可用skills索引
{skills_list_with_dir}

## 执行步骤

### 步骤 0: 上报工具使用记录
**⚠️ 重要：首先必须调用 log_report 工具**
- **[AI Agent Action]**请立即呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
- 参数：work_dir={repo_path}, tool_type=skills_expert

### 步骤 1: skills匹配
请根据上述用户需求和可用skills索引，选择最匹配的skills。考虑：
- skills描述与用户需求的关联度
- skills名称与任务类型的匹配度
- 选择最能满足用户需求的skills

### 步骤 2: 读取详情

选择最佳匹配skills后，**必须使用目录名（dir_name）**来构建路径并读取其详细内容：

```python
from pathlib import Path
matched_skill = [选择的skills对象]
# ⚠️ 重要：必须使用 matched_skill.dir_name 而不是 matched_skill.name 来构建路径
# 因为 name 可能包含中文，而目录名是英文的
skill_path = Path('{repo_path}') / '.joycode' / 'skills' / matched_skill.dir_name / 'SKILL.md'
skill_content = await read_file(skill_path)
```

**注意**：如果技能名称是"Java Controller 生成器"，但目录名是"java-controller-generator"，必须使用目录名来构建路径！

### 步骤 3: 执行skills

根据skillContent中的指导，执行相应的操作来实现用户需求。

### 步骤 4: 检查

- 从模版复制进来的无用代码要删除掉
- 确保代码能正确运行

## 当前上下文

- 项目路径: {repo_path}
- 关联文件: {file_path or '无'}
- 可用skills数量: {len(available_skills)}
- 索引机制: 已启用，支持快速定位

请严格按照以上步骤执行，利用索引机制先匹配skills，然后**使用 dir_name 通过标准路径读取详情**，最后执行skills。
"""
        
        return skill_execution_prompt
        
    except Exception as e:
        error_message = str(e)
        return f"""执行skills时发生错误: {error_message}

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir={repo_path}, tool_type=skills_expert"""


async def handle_skills_expert(
    requirements: Optional[str] = None,
    requirements_file: Optional[str] = None,
    repo_path: str = None
) -> str:
    """
    智能 skills 专家，根据需求描述或需求文件，自动匹配并执行相应的skills来完成任务
    
    Args:
        requirements: 用户需求描述
        requirements_file: 需求文件相对项目根目录的路径
        repo_path: Git 仓库目录（绝对路径）
        
    Returns:
        执行指导提示
    """
    try:
        # 参数验证
        if not requirements and not requirements_file:
            return f"""必须提供 requirements 或 requirements_file 其中之一

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir={repo_path or 'unknown'}, tool_type=skills_expert"""
        
        if not repo_path:
            return """必须提供 repo_path 参数

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir=unknown, tool_type=skills_expert"""
        
        # 获取需求内容
        requirements_content = requirements or ""
        
        if requirements_file:
            file_path = Path(repo_path) / requirements_file
            if file_exists(file_path):
                requirements_content = await read_file(file_path)
            else:
                return f"""需求文件不存在: {requirements_file}

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir={repo_path}, tool_type=skills_expert"""
        
        if not requirements_content.strip():
            return f"""需求内容为空，请提供有效的需求描述或需求文件

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir={repo_path}, tool_type=skills_expert"""
        
        # 匹配并执行
        result = await match_and_execute_skill(
            requirements_content,
            repo_path,
            str(requirements_file) if requirements_file else None
        )
        
        return result
        
    except Exception as e:
        error_message = str(e)
        return f"""Skills 工具执行失败: {error_message}

**[AI Agent Action]**请呼叫「log_report」工具进行本次工具使用记录上报，本次使用工具为skills_expert
参数：work_dir={repo_path or 'unknown'}, tool_type=skills_expert"""
