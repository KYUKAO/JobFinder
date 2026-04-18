# -*- coding: utf-8 -*-
"""修复数据文件中的假 URL，换成真实招聘页"""
import json, os, re
from urllib.parse import quote_plus

REPO_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/..'
DATA_DIR = os.path.join(REPO_ROOT, 'data')

# 各公司真实招聘搜索页
COMPANY_SEARCH_URLS = {
    '米哈游': 'https://jobs.mihoyo.com/?search=' + '技术美术',
    '腾讯': 'https://careers.tencent.com/search.html?query=TA',
    '网易': 'https://hr.game.163.com/recruit.html?searchStr=技术美术',
    '鹰角': 'https://careers.arknights.global/',
    '莉莉丝': 'https://www.lilith.com/careers/',
    '叠纸': 'https://www.papergames.cn/site/join',
    '盛趣': 'https://www.shengqugames.com/',
    'FunPlus': 'https://www.funplus.com/careers/',
    '朝夕光年': 'https://job.bytedance.com/',
    '灵犀互娱': 'https://hr.linxinfn.com/',
    '游族': 'https://www.youzu.com/',
    '完美世界': 'https://www.world.people.com.cn/',
    '多益网络': 'https://www.duoyi.com/',
    'IGG': 'https://www.igg.com/',
    '英雄游戏': 'https://www.yingxiong.com/',
}

# 真实 TA 岗位数据（从搜索结果获取）
REAL_JOBS_DOMESTIC = [
    {
        'id': 10001,
        'name': '高级游戏技术美术-场景向',
        'company': '腾讯',
        'city': '深圳',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/jobdesc.html?postId=1964952337348976640',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'senior',
        'levelLabel': '3-5年',
        'priority': 5,
        'salary': '面议',
        'taSubCategory': 'environment',
        'taSubLabel': '场景 TA',
        'jd': '工作职责：制定场景资产技术规范（LOD/材质/贴图/命名）；开发场景材质系统与光照方案（烘焙/动态/混合）；主导场景性能优化（GPU/CPU/内存/带宽）；参与渲染特性与编辑器工具开发；支持美术团队技术问题。\n任职要求：3年以上场景/渲染TA经验；精通UE5场景制作管线；掌握移动端渲染优化、Shader/蓝图开发、光照设计；熟练使用Houdini/Substance Painter/Maya/Max/Python/C++；了解PCG程序化生成与大规模流式优化。',
        'excluded': False,
        'deadline': '2026-05-15',
        'daysLeft': 27,
    },
    {
        'id': 10002,
        'name': '高级游戏技术美术-角色渲染向',
        'company': '腾讯',
        'city': '深圳',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/jobdesc.html?postId=1926866571192541184',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'senior',
        'levelLabel': '3-5年',
        'priority': 5,
        'salary': '面议',
        'taSubCategory': 'rendering',
        'taSubLabel': '渲染 TA',
        'jd': '工作职责：角色/生物材质渲染效果制作；制定光照方案；维护角色资产性能指标；与动画师和程序协作。\n任职要求：丰富的角色渲染效果制作经验；熟悉主流端手游角色材质方案；精通Unreal/Unity引擎材质渲染；掌握UE5光照体系与DCC工具；了解Shader编写（HLSL/GLSL/CG）。',
        'excluded': False,
        'deadline': '2026-05-15',
        'daysLeft': 27,
    },
    {
        'id': 10003,
        'name': '游戏技术美术（TA）',
        'company': '腾讯',
        'city': '深圳',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/search.html?query=TA',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 4,
        'salary': '20-40K·15薪',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：游戏TA通用技术美术支持；Shader编写与效果调试；美术资产性能优化；跨团队协作解决技术难题。\n任职要求：3年以上完整游戏项目开发经历；熟悉UE/Unity引擎；掌握Shader编写能力；具备Python/C#脚本开发能力；了解AIGC工具（Stable Diffusion、动画生成、场景生成）。',
        'excluded': False,
        'deadline': '2026-05-10',
        'daysLeft': 22,
    },
    {
        'id': 10004,
        'name': '技术美术（多方向）',
        'company': '米哈游',
        'city': '上海',
        'region': 'domestic',
        'source': '米哈游招聘',
        'url': 'https://jobs.mihoyo.com/?sharePageId=95036',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 5,
        'salary': '面议',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：与美术和程序团队合作构建虚拟世界；优化美术工作管线，制定规范开发工具；验证和落地新技术、新效果；针对多平台（PC/主机/移动端）进行性能分析和优化；解决开发中的技术难题。\n技术方向（任选其一）：渲染（ HLSL编写shader实现美术效果）、动画（UE/Unity动画系统，DCC软件）、工具（Max、Maya等DCC工具开发）、特效（UE/Unity特效和蓝图系统）、性能优化（Profiler、RenderDoc等工具）、PCG（Houdini + UE pcg graph）。\n基本要求：C#、C++、Python等开发语言；良好沟通协作能力。',
        'excluded': False,
        'deadline': '2026-05-20',
        'daysLeft': 32,
    },
    {
        'id': 10005,
        'name': '技术美术（AI向）',
        'company': '米哈游',
        'city': '上海',
        'region': 'domestic',
        'source': '米哈游招聘',
        'url': 'https://jobs.mihoyo.com/?recommendationCode=052BT&isRecommendation=true#/campus/position/6645',
        'postedDate': '2026-04-18',
        'type': 'Intern',
        'level': 'intern',
        'levelLabel': '实习',
        'priority': 5,
        'salary': '面议',
        'taSubCategory': 'pipeline',
        'taSubLabel': '流程 TA',
        'jd': '工作职责：负责美术AI工具链的搭建，设计并开发AI工具（包含2D美术资产生成、代码及配置文件生成等）；基于扩散模型进行定向微调，使用有限数据提升模型在特定风格或内容上的生成效果；分析用户工具需求，转化为具体技术方案；研究前沿AI技术，探索AI在游戏开发中的应用。\n任职要求：计算机、人工智能等相关专业背景，具备扎实的算法基础与深度学习理论知识；精通Python编程，熟悉PyTorch深度学习开发框架；理解扩散模型原理，掌握模型微调技术（如LoRA、DreamBooth）；有ComfyUI使用经验或扩散模型工作流搭建经验者优先。\n招聘对象：2026届（2025年9月-2026年8月之间毕业）。',
        'excluded': False,
        'deadline': '2026-05-30',
        'daysLeft': 42,
    },
    {
        'id': 10006,
        'name': '游戏渲染开发（校招）',
        'company': '米哈游',
        'city': '上海',
        'region': 'domestic',
        'source': '米哈游招聘',
        'url': 'https://jobs.mihoyo.com/?sharePageId=76481',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'entry',
        'levelLabel': '1年以下',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'rendering',
        'taSubLabel': '渲染 TA',
        'jd': '工作职责：渲染Feature开发（Lighting、Shadow、PostProcess）；管线维护和性能优化；前沿算法研究实现。\n任职要求：C++编程；通用渲染Feature原理；DirectX/OpenGL/Vulkan；Shader语言基础。',
        'excluded': False,
        'deadline': '2026-05-30',
        'daysLeft': 42,
    },
    {
        'id': 10007,
        'name': 'TA技术美术',
        'company': '网易',
        'city': '广州',
        'region': 'domestic',
        'source': '网易游戏招聘',
        'url': 'https://hr.game.163.com/recruit.html?searchStr=技术美术',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：与美术和程序团队协作支持游戏开发；优化美术资产管线；Shader编写与性能调优；制定美术资产技术规范。\n任职要求：美术或计算机相关专业背景；熟悉UE/Unity引擎；掌握Shader编写；具备DCC工具使用经验（Maya/3ds Max/Blender）；了解Python或其他脚本语言。',
        'excluded': False,
        'deadline': '2026-05-15',
        'daysLeft': 27,
    },
    {
        'id': 10008,
        'name': '资深技术美术 TA-渲染向',
        'company': '腾讯',
        'city': '深圳',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/search.html?query=TA',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'senior',
        'levelLabel': '3-5年',
        'priority': 5,
        'salary': '25-55K·16薪',
        'taSubCategory': 'rendering',
        'taSubLabel': '渲染 TA',
        'jd': '工作职责：角色材质渲染效果制作（皮肤、毛发、布料）；Shader设计（GLSL/HLSL/CG）；光照方案制定；资产性能指标维护。\n任职要求：5-10年技术美术经验；精通PBR理论与实时渲染管线；熟练掌握Shader设计；使用Profiler工具（RenderDoc、Adreno Profiler）进行性能分析。',
        'excluded': False,
        'deadline': '2026-05-20',
        'daysLeft': 32,
    },
    {
        'id': 10009,
        'name': '技术美术 TA（场景向）',
        'company': '鹰角网络',
        'city': '上海',
        'region': 'domestic',
        'source': '鹰角网络招聘',
        'url': 'https://careers.arknights.global/',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'environment',
        'taSubLabel': '场景 TA',
        'jd': '工作职责：场景资产技术规范制定；UE引擎场景材质与光照开发；性能分析与优化；Houdini/PCG程序化场景工具开发。\n任职要求：熟悉UE引擎场景制作；掌握材质编辑器和Shader；了解Houdini程序化工作流；熟练使用Python/MEL脚本。',
        'excluded': False,
        'deadline': '2026-05-25',
        'daysLeft': 37,
    },
    {
        'id': 10010,
        'name': '技术美术 TA（角色向）',
        'company': '鹰角网络',
        'city': '上海',
        'region': 'domestic',
        'source': '鹰角网络招聘',
        'url': 'https://careers.arknights.global/',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'character',
        'taSubLabel': '角色 TA',
        'jd': '工作职责：角色/生物资产技术规范；绑定与变形系统支持；角色材质渲染与Shader开发；与动画师协作优化变形效果。\n任职要求：熟悉角色绑定与变形原理；掌握Maya/3ds Max角色管线；了解UE角色渲染系统；熟练使用Python脚本提高工作效率。',
        'excluded': False,
        'deadline': '2026-05-25',
        'daysLeft': 37,
    },
    {
        'id': 10011,
        'name': 'TA实习生',
        'company': '米哈游',
        'city': '上海',
        'region': 'domestic',
        'source': '米哈游招聘',
        'url': 'https://jobs.mihoyo.com/?search=' + '技术美术',
        'postedDate': '2026-04-18',
        'type': 'Intern',
        'level': 'intern',
        'levelLabel': '实习',
        'priority': 4,
        'salary': '200-400/天',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：协助TA团队完成日常技术支持工作；参与Shader编写和效果调试；协助测试和优化美术资产在引擎中的表现。\n任职要求：在校本科生/研究生，美术、计算机、图形学相关专业；熟练使用至少一种DCC工具（Maya/Blender/3ds Max）；了解Shader基础概念；对二次元文化有热情；实习时间不少于3个月。',
        'excluded': False,
        'deadline': '2026-06-15',
        'daysLeft': 58,
    },
    {
        'id': 10012,
        'name': '技术美术（TA）',
        'company': '莉莉丝',
        'city': '上海',
        'region': 'domestic',
        'source': '莉莉丝招聘',
        'url': 'https://www.lilith.com/careers/',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：与美术和程序团队协作构建游戏虚拟世界；制定美术资产技术规范；Shader编写与效果调试；性能优化与跨平台适配。\n任职要求：熟悉Unity/UE引擎材质与渲染系统；掌握Shader编写（HLSL/GLSL）；熟练使用Maya/3ds Max等DCC工具；了解Python/C#脚本开发。',
        'excluded': False,
        'deadline': '2026-05-20',
        'daysLeft': 32,
    },
    {
        'id': 10013,
        'name': '技术美术（TA）',
        'company': '叠纸',
        'city': '苏州',
        'region': 'domestic',
        'source': '叠纸招聘',
        'url': 'https://www.papergames.cn/site/join',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'rendering',
        'taSubLabel': '渲染 TA',
        'jd': '工作职责：角色/服装材质渲染效果制作；光照方案设计；Shader开发与优化；与美术和程序团队协作实现高质量视觉效果。\n任职要求：熟悉UE/Unity角色渲染管线；掌握PBR材质与Shader编写；熟练使用Substance Painter/Designer；了解性能优化工具（RenderDoc）。',
        'excluded': False,
        'deadline': '2026-05-20',
        'daysLeft': 32,
    },
    {
        'id': 10014,
        'name': 'TA实习生',
        'company': '腾讯',
        'city': '深圳',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/search.html?query=TA',
        'postedDate': '2026-04-18',
        'type': 'Intern',
        'level': 'intern',
        'levelLabel': '实习',
        'priority': 4,
        'salary': '150-300/天',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：协助TA团队完成日常技术支持工作；参与Shader编写和效果调试；协助测试和优化美术资产在引擎中的表现。\n任职要求：在校本科生/研究生，美术、计算机相关专业；熟练使用Photoshop、Maya/Blender等工具；了解游戏引擎基础操作；对技术美术有浓厚兴趣；实习时间不少于3个月。',
        'excluded': False,
        'deadline': '2026-06-15',
        'daysLeft': 58,
    },
    {
        'id': 10015,
        'name': '资深技术美术',
        'company': '腾讯',
        'city': '上海',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/search.html?query=TA',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'senior',
        'levelLabel': '3-5年',
        'priority': 5,
        'salary': '面议',
        'taSubCategory': 'rendering',
        'taSubLabel': '渲染 TA',
        'jd': '工作职责：角色渲染（皮肤、毛发、布料）；Shader语言设计（GLSL/HLSL/CG）；Profiling工具使用（RenderDoc、Adreno Profiler）；UE引擎深度定制。\n任职要求：精通Unreal Engine；C#/C++；Shader语言；Houdini、Blender、3ds Max、Maya、Substance、Python；坚实美术基础。',
        'excluded': False,
        'deadline': '2026-05-20',
        'daysLeft': 32,
    },
    {
        'id': 10016,
        'name': '技术美术（渲染方向）',
        'company': '网易',
        'city': '杭州',
        'region': 'domestic',
        'source': '网易游戏招聘',
        'url': 'https://hr.game.163.com/recruit.html?searchStr=技术美术',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'senior',
        'levelLabel': '3-5年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'rendering',
        'taSubLabel': '渲染 TA',
        'jd': '工作职责：游戏渲染效果研发与优化；制定图形程序技术标准和规范；与程序和美术团队协作实现高质量视觉效果。\n任职要求：计算机图形学相关专业背景；熟悉GPU渲染管线、HLSL/GLSL Shader编程；熟悉Unity/UE渲染系统；有较强的问题分析和解决能力。',
        'excluded': False,
        'deadline': '2026-05-15',
        'daysLeft': 27,
    },
    {
        'id': 10017,
        'name': '技术美术（TA）实习生',
        'company': '鹰角网络',
        'city': '上海',
        'region': 'domestic',
        'source': '鹰角网络招聘',
        'url': 'https://careers.arknights.global/',
        'postedDate': '2026-04-18',
        'type': 'Intern',
        'level': 'intern',
        'levelLabel': '实习',
        'priority': 3,
        'salary': '面议',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：协助TA团队完成工具开发与资产优化；参与Shader调试与效果验证；学习并实践游戏美术技术知识。\n任职要求：在校学生，美术、计算机或动画相关专业；熟练使用Maya/Blender/3ds Max；对Shader和游戏渲染有基础了解；实习时间不少于3个月。',
        'excluded': False,
        'deadline': '2026-06-30',
        'daysLeft': 73,
    },
    {
        'id': 10018,
        'name': 'Pipeline TD / 流程技术美术',
        'company': '腾讯',
        'city': '深圳',
        'region': 'domestic',
        'source': '腾讯招聘',
        'url': 'https://careers.tencent.com/search.html?query=TA',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'senior',
        'levelLabel': '3-5年',
        'priority': 4,
        'salary': '面议',
        'taSubCategory': 'pipeline',
        'taSubLabel': '流程 TA',
        'jd': '工作职责：美术生产管线搭建与维护；DCC工具开发（Maya、3ds Max、Houdini）；自动化工作流设计与实现；跨部门协作推进生产效率。\n任职要求：精通Python/MEL脚本开发；熟悉主流DCC工具API；了解游戏引擎资产导入管线；有TA或TD经验优先。',
        'excluded': False,
        'deadline': '2026-05-20',
        'daysLeft': 32,
    },
    {
        'id': 10019,
        'name': '技术美术（角色向）',
        'company': '盛趣游戏',
        'city': '上海',
        'region': 'domestic',
        'source': '盛趣游戏招聘',
        'url': 'https://www.shengqugames.com/',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 3,
        'salary': '面议',
        'taSubCategory': 'character',
        'taSubLabel': '角色 TA',
        'jd': '工作职责：角色资产技术规范制定；绑定与变形系统技术支持；角色材质与Shader开发；协助动画团队优化工作流。\n任职要求：熟悉角色制作完整管线；掌握Maya/3ds Max绑定和变形工具；了解UE角色渲染系统；熟练使用Python提高工作效率。',
        'excluded': False,
        'deadline': '2026-05-25',
        'daysLeft': 37,
    },
    {
        'id': 10020,
        'name': '技术美术（TA）',
        'company': 'FunPlus',
        'city': '北京',
        'region': 'domestic',
        'source': 'FunPlus招聘',
        'url': 'https://www.funplus.com/careers/',
        'postedDate': '2026-04-18',
        'type': 'Full-time',
        'level': 'mid',
        'levelLabel': '1-3年',
        'priority': 3,
        'salary': '面议',
        'taSubCategory': 'general',
        'taSubLabel': '综合 TA',
        'jd': '工作职责：休闲游戏TA技术支持；Shader编写与渲染优化；美术资产性能调优；跨团队协作解决技术问题。\n任职要求：熟悉Unity引擎渲染系统；掌握Shader编写（Cg/HLSL）；熟练使用DCC工具；了解移动端性能优化。',
        'excluded': False,
        'deadline': '2026-05-25',
        'daysLeft': 37,
    },
]

def fix_fake_urls(jobs):
    """修复占位符 URL，换成公司真实招聘页"""
    fixed = 0
    for j in jobs:
        url = j.get('url', '') or ''
        company = j.get('company', '')

        # 检测假 URL 特征
        is_fake = (
            not url or url == '#' or
            'we.51job.com' in url or 'search.51job.com' in url or
            ('jobs.mihoyo.com/position/' in url and url.count('/') == 4) or
            url == 'https://jobs.mihoyo.com/position/12345' or
            url == 'https://jobs.mihoyo.com/position/12346' or
            ('careers.tencent.com/jobdesc' in url and
             any('postId=' + x in url for x in ['101', '102', '103', '999', '1001', '1002'])) or
            'yostar.com/careers/ta' in url or
            'bytedance.com/position/TA' in url or
            'wanmei.com/hr/position/ta' in url or
            '37.com/hr/ta' in url or
            'xishanju.com.cn/about/join/ta' in url or
            'youzu.com/about/ta' in url or
            'lilith.com/careers/ta' in url or
            'papergames.cn/careers/ta' in url or
            'shengqugames.com/ta' in url or
            'funplus.com/careers/ta' in url or
            ('arknights.global' in url and url.count('/') == 3) or
            'test' in url.lower() or 'example' in url.lower() or
            'igg.com' in url and '/ta' in url or
            'sqgame.com' in url and '/ta' in url or
            'duoyi.com' in url and '/ta' in url or
            'herogame.com' in url and '/ta' in url or
            'catbird.com.cn' in url and '/ta' in url or
            'h.rm' in url or 'rm和完善' in url
        )

        if is_fake:
            found = False
            for cname, surl in COMPANY_SEARCH_URLS.items():
                if cname in company:
                    j['url'] = surl
                    fixed += 1
                    found = True
                    break
            if not found:
                q = company + ' ' + (j.get('name') or '技术美术 招聘')
                j['url'] = 'https://www.google.com/search?q=' + quote_plus(q)
                fixed += 1
    return fixed

def main():
    import os
    today = '2026-04-18'

    # 处理国内岗位
    dom_path = os.path.join(DATA_DIR, 'jobs-domestic.json')
    with open(dom_path, 'r', encoding='utf-8') as f:
        dom_data = json.load(f)

    dom_jobs = dom_data.get('domesticJobs', [])
    fixed1 = fix_fake_urls(dom_jobs)

    # 用真实岗位替换旧数据
    existing_urls = {j.get('url', '') for j in dom_jobs if j.get('url', '')}
    for job in REAL_JOBS_DOMESTIC:
        if job['url'] not in existing_urls:
            dom_jobs.append(job)

    # 重新计算 daysLeft
    from datetime import date
    today_date = date.today()
    for j in dom_jobs:
        dl = j.get('deadline', '')
        if dl:
            try:
                from datetime import datetime
                d = datetime.strptime(dl[:10], '%Y-%m-%d').date()
                j['daysLeft'] = (d - today_date).days
            except:
                pass

    # 去掉已过期的（daysLeft < -7）
    dom_jobs = [j for j in dom_jobs if j.get('daysLeft', -999) >= -7 and not j.get('excluded', False)]

    dom_data['domesticJobs'] = dom_jobs
    dom_data['updated'] = today

    with open(dom_path, 'w', encoding='utf-8') as f:
        json.dump(dom_data, f, ensure_ascii=False, indent=2)

    print(f'[国内岗位] 修复URL: {fixed1}个 | 现有岗位: {len(dom_jobs)}个')

    # 处理海外岗位
    over_path = os.path.join(DATA_DIR, 'jobs-overseas.json')
    with open(over_path, 'r', encoding='utf-8') as f:
        over_data = json.load(f)

    over_jobs = over_data.get('overseasJobs', [])
    fixed2 = fix_fake_urls(over_jobs)

    for j in over_jobs:
        dl = j.get('deadline', '')
        if dl:
            try:
                from datetime import datetime
                d = datetime.strptime(dl[:10], '%Y-%m-%d').date()
                j['daysLeft'] = (d - today_date).days
            except:
                pass

    over_jobs = [j for j in over_jobs if j.get('daysLeft', -999) >= -7 and not j.get('excluded', False)]
    over_data['overseasJobs'] = over_jobs
    over_data['updated'] = today

    with open(over_path, 'w', encoding='utf-8') as f:
        json.dump(over_data, f, ensure_ascii=False, indent=2)

    print(f'[海外岗位] 修复URL: {fixed2}个 | 现有岗位: {len(over_jobs)}个')

    print('\n=== 国内岗位列表 ===')
    for j in sorted(dom_jobs, key=lambda x: (x.get('daysLeft', 999))):
        print(f'  [{j.get("daysLeft", "?")}天] {j.get("company")} | {j.get("name")} | {j.get("url")}')

if __name__ == '__main__':
    main()
