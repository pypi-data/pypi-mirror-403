import time
import random
import os
import minify_html
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup
from curl_cffi import requests
from lxml import html, etree
import base64
from PIL import Image
import io

compress_html_js = """
function getSimplifiedDOM(node) {
    // 1. 处理文本节点
    if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent.trim();
        return text ? text.slice(0, 100) + (text.length > 100 ? '...' : '') : null;
    }

    // 2. 过滤无用标签
    const ignoreTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME', 'SVG', 'LINK', 'META'];
    if (ignoreTags.includes(node.tagName)) return null;
    if (node.nodeType !== Node.ELEMENT_NODE) return null;

    // 3. 过滤不可见元素
    // 【注意】这里声明了第一次 style
    const style = window.getComputedStyle(node);
    
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return null;
    
    // 过滤宽高太小的元素（往往是埋点空像素）
    const rect = node.getBoundingClientRect();
    
    // 【修复点】删除了这里重复的 const style = ... 代码
    // 直接使用上面已经定义好的 style 变量即可
    
    // 如果宽高为0，但溢出可见，说明可能有定位的子元素显示在外面
    if ((rect.width === 0 || rect.height === 0) && style.overflow !== 'visible') return null;

    // --- 开始构建标签字符串 ---
    const tagName = node.tagName.toLowerCase();
    let tagStr = tagName;

    // A. 基础标识符 (ID 和 Class)
    if (node.id) tagStr += `#${node.id}`;
    if (node.className && typeof node.className === 'string') {
        const classes = node.className.trim().split(/\s+/);
        if (classes.length > 0) tagStr += `.${classes.join('.')}`;
    }

    // B. 关键属性白名单
    const props = [];

    // 通用重要属性
    if (node.getAttribute('role')) props.push(`role="${node.getAttribute('role')}"`);
    if (node.getAttribute('aria-label')) props.push(`aria-label="${node.getAttribute('aria-label')}"`);
    if (node.getAttribute('title')) props.push(`title="${node.getAttribute('title')}"`);
    // 建议增加这个，很多弹窗用这个属性
    if (node.getAttribute('aria-modal')) props.push(`aria-modal="${node.getAttribute('aria-modal')}"`);

    // 特定标签的特定属性
    if (tagName === 'a') {
        const href = node.getAttribute('href');
        if (href && !href.startsWith('javascript')) props.push(`href="${href}"`);
    } else if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
        if (node.getAttribute('type')) props.push(`type="${node.getAttribute('type')}"`);
        if (node.getAttribute('name')) props.push(`name="${node.getAttribute('name')}"`);
        if (node.getAttribute('placeholder')) props.push(`placeholder="${node.getAttribute('placeholder')}"`);
        if (node.disabled) props.push('disabled');
        if (node.checked) props.push('checked');
    } else if (tagName === 'button') {
        if (node.getAttribute('type')) props.push(`type="${node.getAttribute('type')}"`);
    } else if (tagName === 'img') {
        if (node.getAttribute('alt')) props.push(`alt="${node.getAttribute('alt')}"`);
    } else if (tagName === 'dialog') {
        // 保留 open 属性
        if (node.open) props.push('open');
    }

    if (props.length > 0) {
        tagStr += ` ${props.join(' ')}`;
    }

    // 4. 递归子节点 (包含 Shadow DOM 处理)
    let childNodes = Array.from(node.childNodes);
    if (node.shadowRoot) {
        childNodes = [...childNodes, ...Array.from(node.shadowRoot.childNodes)];
    }
    
    const children = childNodes
        .map(getSimplifiedDOM)
        .filter(n => n !== null);
    
    // 5. 组装输出
    if (children.length === 0) {
        return `<${tagStr} />`;
    }
    return `<${tagStr}>${children.join('')}</${tagName}>`; 
}

return getSimplifiedDOM(document.body);
"""


# 使用requests获取html，用于测试是否使用了瑞数和jsl
def requests_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    }
    response = requests.get(url, headers=headers, verify=False)
    response.encoding = "utf-8"
    return response.text, response.status_code


# 使用dp无头模式获取html，用于测试是否使用了其他waf，如移动waf
def dp_headless_html(url):
    opt = ChromiumOptions().headless(True)
    opt.set_argument('--no-sandbox')
    """创建新的浏览器实例"""
    random_port = random.randint(9934, 10034)
    custom_data_dir = os.path.join(os.path.expanduser('~'), 'DrissionPage', "userData", f"{random_port}")
    opt.set_user_data_path(custom_data_dir)  # 设置用户数据路径
    opt.set_local_port(random_port)
    page = ChromiumPage(opt)
    tab = page.latest_tab
    tab.get(url)
    # todo: 目前没有更好的方式，为了数据渲染完全，只能硬等【受网速波动影响比较大】
    time.sleep(10)
    page_html = tab.html
    # 无头浏览器在用完之后一定要记得再page级别进行quit
    page.quit()
    return page_html


# 压缩html
def compress_html(content, only_text=False):
    doc = html.fromstring(content)
    # 删除 style 和 script 标签
    for element in doc.xpath('//style | //script'):
        element.getparent().remove(element)

    # 删除 link 标签
    for link in doc.xpath('//link[@rel="stylesheet"]'):
        link.getparent().remove(link)

    # 删除 meta 标签（新增功能）
    for meta in doc.xpath('//meta'):
        meta.getparent().remove(meta)

    for svg in doc.xpath('//svg'):
        # 获取 SVG 内的文本内容
        text_content = svg.text_content()
        # 创建一个新的文本节点替换 SVG
        parent = svg.getparent()
        if parent is not None:
            parent.text = (parent.text or '') + text_content
            parent.remove(svg)

    # 删除 style 属性
    for element in doc.xpath('//*[@style]'):
        element.attrib.pop('style')

    # 删除所有 on* 事件属性
    for element in doc.xpath('//*'):
        for attr in list(element.attrib.keys()):
            if attr.startswith('on'):
                element.attrib.pop(attr)

    result = etree.tostring(doc, encoding='unicode')
    result = minify_html.minify(result)
    compress_rate = round(len(content) / len(result) * 100)
    print(f"html压缩比=> {compress_rate}%")
    if not only_text:
        return result, compress_rate
    soup = BeautifulSoup(result, 'html.parser')
    result = soup.get_text(strip=True)
    return result, compress_rate


# 通过cookie判断是否有waf，需要通过遇到的例子，不断的完善cookie判别函数
def assert_waf_cookie(cookies: list):
    for cookie in cookies:
        cookie_name = cookie['name']
        cookie_value = cookie['value']
        if len(cookie_name) == 13 and len(cookie_value) == 88:
            return True, "瑞数"
        if "_jsl" in cookie_name:
            return True, "加速乐"
    return False, "没有waf"


# 对dp_mcp的消息打包
def dp_mcp_message_pack(message: str, **kwargs):
    text_obj = {key: value for key, value in kwargs.items()}
    text_obj.update({"message": message})
    return {
        "content": [{
            "type": "text",
            # "text": json.dumps(text_obj, ensure_ascii=False)
            "text": text_obj
        }]
    }


def btyes2Base64Img(target_byte):
    """
    把byte转为base64，用于传输图片
    :param target_byte:
    :return:
    """
    return "data:image/png;base64," + base64.b64encode(target_byte).decode()


def compress_image_bytes(input_bytes, target_size_mb=1):
    """
    压缩图片字节数据到目标大小

    参数:
        input_bytes: 输入图片的字节数据
        target_size_mb: 目标大小(MB)，默认1MB

    返回:
        压缩后的图片字节数据
    """
    target_size = target_size_mb * 1024 * 1024  # 转换为字节

    # 从字节数据打开图片
    img = Image.open(io.BytesIO(input_bytes))

    # 如果是PNG或其他格式，转换为RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')

    # 初始质量设置
    quality = 95

    # 先尝试压缩
    output_buffer = io.BytesIO()
    img.save(output_buffer, 'JPEG', quality=quality, optimize=True)
    output_bytes = output_buffer.getvalue()

    # 如果文件仍然太大，逐步降低质量
    while len(output_bytes) > target_size and quality > 10:
        quality -= 5
        output_buffer = io.BytesIO()
        img.save(output_buffer, 'JPEG', quality=quality, optimize=True)
        output_bytes = output_buffer.getvalue()

    # 如果降低质量还不够，尝试缩小尺寸
    if len(output_bytes) > target_size:
        width, height = img.size

        while len(output_bytes) > target_size and quality > 10:
            # 缩小10%
            width = int(width * 0.9)
            height = int(height * 0.9)
            img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
            output_buffer = io.BytesIO()
            img_resized.save(output_buffer, 'JPEG', quality=quality, optimize=True)
            output_bytes = output_buffer.getvalue()

    final_size = len(output_bytes) / (1024 * 1024)
    # print(f"压缩完成！")
    # print(f"原始大小: {len(input_bytes) / (1024 * 1024):.2f}MB")
    # print(f"压缩后大小: {final_size:.2f}MB")
    # print(f"最终质量: {quality}")

    return output_bytes

# todo: 大致盘一下各种判定的逻辑【以下的所有压缩比之间的差距均取“绝对值”】
#  1. 如果requests、无头、有头获取到的压缩比之间从差距都在15%以内，则认定该页面是静态页面，此时优先使用requests请求
#  2. 如果requests的status_code为特定的412，或者521，则判定是瑞数和jsl。[此时还有一个特点：requests的压缩比会与其他两种方式获取到的压缩比差距非常大(一两千的那种)]
#  3. 如果requests、无头、有头获取到的压缩比之间差距都在40%以上，则判定该页面只可以用有头采集
#  4. 如果无头和有头获取到的压缩比之间差距小于15%，但是requests和无头的差距大于40%，则认定该页面可以使用无头浏览器采集
#  5. 如果requests和有头获取到的压缩比之间差距小于15%，但是无头和有头的差距大于40%，则认定该页面优先使用有头浏览器采集
#  【此时可能是：1.使用了别的检测无头的waf。2.网站使用瑞数，但是这次请求没有拦截requests（不知道是不是瑞数那边故意设置的），
#   此时如果想进一步判定是否是瑞数，可以使用有头浏览器取一下cookies，如果cookies里面存在瑞数的cookie，那么就可以断定是瑞数】
