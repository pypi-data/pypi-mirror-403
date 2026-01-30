import re


from typing import List

def extract_tag_content(xml_text: str, tag_name: str, case_sensitive: bool = False) -> List[str]:
    """
    从XML文本中提取指定标签的内容（基于正则表达式）
    
    参数:
        xml_text: XML格式的字符串
        tag_name: 要提取的标签名称
        case_sensitive: 是否区分大小写（默认不区分）
    
    返回:
        包含所有匹配内容的字符串列表（按出现顺序）
        如果未找到匹配项，返回空列表
    
    注意:
        此方法适用于结构简单的XML场景，对于复杂XML建议使用xml.etree.ElementTree
    """
    # 根据大小写敏感设置标志
    flags = re.DOTALL
    if not case_sensitive:
        flags |= re.IGNORECASE
    
    # 构建正则模式：支持标签属性，使用非贪婪匹配
    # 模式说明:
    #   <tag_name\b[^>]*>  - 匹配开始标签（支持属性）
    #   (.*?)              - 非贪婪捕获标签内容
    #   </tag_name\s*>     - 匹配结束标签（允许空白）
    pattern = rf'<{re.escape(tag_name)}\b[^>]*>(.*?)</{re.escape(tag_name)}\s*>'
    
    # 查找所有匹配项
    matches = re.findall(pattern, xml_text, flags)
    
    # 清理提取的内容（去除首尾空白）
    return [match.strip() for match in matches]


if __name__ == "__main__":
    # ==================== 使用示例 ====================
    # 示例1：提取<conclusion>标签内容
    xml_sample = """
    <conclusion>
    - [用简洁的几句话概括：  
    - 问题的真实成因（基于日志与代码的联合分析）  
    - 涉及的关键模块/函数  
    - 当前行为是正常还是异常，以及判断依据  
    - 如某些怀疑路径被排除，简要说明"排除理由"]
    </conclusion>
    """

    results = extract_tag_content(xml_sample, "conclusion")
    print("提取结果:", results[0] if results else "未找到匹配内容")

    # 示例2：处理包含属性的标签
    xml_with_attrs = """
    <error type="critical" code="500">
        <message>系统异常</message>
        <stacktrace>NullPointerException at...</stacktrace>
    </error>
    """

    messages = extract_tag_content(xml_with_attrs, "message")
    stacktraces = extract_tag_content(xml_with_attrs, "stacktrace")
    print(f"错误信息: {messages}")
    print(f"堆栈跟踪: {stacktraces}")

    # 示例3：提取多个相同标签
    xml_multiple = """
    <items>
        <item>第一项</item>
        <item>第二项</item>
        <item>第三项</item>
    </items>
    """

    items = extract_tag_content(xml_multiple, "item")
    print(f"提取的项数: {len(items)}")
    for i, item in enumerate(items, 1):
        print(f"  第{i}项: {item}")

    # 示例4：不区分大小写提取
    xml_mixed_case = "<Conclusion>混合大小写内容</Conclusion>"
    conclusion = extract_tag_content(xml_mixed_case, "conclusion")  # 默认不区分大小写
    print(f"不区分大小写提取: {conclusion}")
