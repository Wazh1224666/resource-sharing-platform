"""
考研资料全自动爬虫 - download.chinakaoyan.com
功能：自动注册/登录、爬取资源列表、提取下载链接、下载文件
"""
import requests
from bs4 import BeautifulSoup
import re
import os
import time
import json
import ddddocr

BASE_URL = "https://download.chinakaoyan.com"
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": BASE_URL + "/",
}

s = requests.Session()
s.headers.update(HEADERS)

# ========== 工具函数 ==========

def fetch(url, encoding="utf-8-sig"):
    resp = s.get(url, timeout=15)
    resp.encoding = encoding
    return resp

def safe_text(text):
    """清理文本中的控制字符"""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

# ========== 验证码处理 ==========

ocr = ddddocr.DdddOcr(show_ad=False)

def get_captcha():
    """获取并识别验证码，返回5位数字验证码"""
    resp = s.get(BASE_URL + "/authimg.php?act=chkcode&t=" + str(int(time.time() * 1000)), timeout=15)

    code = ocr.classification(resp.content)
    # 验证码为纯数字，只保留数字
    code = re.sub(r'[^0-9]', '', code).strip()[:5]

    if len(code) < 4:
        # 降级：尝试用 OpenCV 预处理
        try:
            import cv2
            import numpy as np
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (0, 0), fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
            _, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
            _, buffer = cv2.imencode('.png', img)
            code2 = ocr.classification(buffer.tobytes())
            code2 = re.sub(r'[^0-9]', '', code2).strip()[:5]
            if len(code2) > len(code):
                code = code2
        except ImportError:
            pass

    return code

# ========== 账号处理 ==========

def try_register(username=None, password="Auto123456!", retries=3):
    """尝试注册账号（不保证成功）"""
    if username is None:
        username = f"auto_dl_{int(time.time()) % 10000}"

    for attempt in range(retries):
        code = get_captcha()
        print(f"[*] 验证码识别结果: {code} (第{attempt+1}次)")

        resp = s.post(BASE_URL + "/user.html", data={
            "usernameu": username,
            "passwordu": password,
            "authinputu": code,
            "act": "login",
            "redirect": "/user.html?act=reg"
        }, timeout=15)
        resp.encoding = "utf-8-sig"

        # 短响应可能表示成功
        if len(resp.text) < 100:
            print(f"[+] 账号注册/登录成功: {username}")
            return True, username, password

        # 检查错误信息
        soup = BeautifulSoup(resp.text, "lxml")
        err_text = soup.get_text()

        if "密码" in err_text or "账号" in err_text:
            print(f"[!] 账号或密码错误 (该接口仅用于登录，不支持自动注册)")
            return False, username, password

        print(f"[!] 验证码错误/注册失败，重试...")

    print("[!] 注册失败次数过多，跳过")
    return False, username, password

def try_login(username, password, retries=8):
    """尝试登录（手机号+密码）"""

    # 先访问登录页，初始化PHP会话
    s.get(f"{BASE_URL}/user.html?act=loginphone", timeout=15)

    for attempt in range(retries):
        code = get_captcha()
        print(f"[*] 登录验证码: '{code}' (第{attempt+1}次)")

        if len(code) < 4:
            print(f"[!] 验证码太短，重试...")
            continue

        resp = s.post(BASE_URL + "/user.html", data={
            "mobilephoneu": username,
            "passwordu": password,
            "authinputu": code,
            "act": "login2",
            "redirect": "/user.html?act=loginphone"
        }, timeout=15)
        resp.encoding = "utf-8-sig"

        # 检查登录成功（响应中包含"登录成功"字样）
        if "登录成功" in resp.text:
            print(f"[+] 登录成功: {username}")

            # 验证登录状态 - 访问用户中心
            verify = s.get(f"{BASE_URL}/user.html?act=loginphone", timeout=15)
            verify.encoding = "utf-8-sig"
            if username[:3] in verify.text or "退出" in verify.text or "个人" in verify.text:
                print(f"[+] 登录状态已确认")
            else:
                print(f"[?] 登录可能未完全生效，将尝试继续...")

            return True, username, password

        soup = BeautifulSoup(resp.text, "lxml")
        err_text = soup.get_text()

        if "密码" in err_text and "错误" in err_text:
            print(f"[!] 密码错误")
            return False, username, password

        print(f"[!] 验证码错误，重试...")
        time.sleep(1.5)

    print("[!] 登录失败次数过多")
    return False, username, password

# ========== 资源爬取 ==========

def parse_homepage():
    """解析首页，提取三个板块的资源列表"""
    print("\n" + "=" * 60)
    print("正在爬取首页资源列表...")
    print("=" * 60)

    resp = fetch(BASE_URL + "/")
    soup = BeautifulSoup(resp.text, "lxml")

    sections = soup.select(".xz20 > .xz21 > .xz23")
    section_names = ["热门推荐资料", "本月热门下载", "最新上传资料", "总下载排行"]
    all_data = {}

    for i, section in enumerate(sections):
        if i >= len(section_names):
            break

        name = section_names[i]
        items = []
        li_list = section.select(".xz26 ul li")

        j = 0
        while j < len(li_list):
            li = li_list[j]
            classes = li.get("class", [])

            if "xz27" in classes:
                a_tag = li.find("a")
                title = safe_text(a_tag.get_text(strip=True)) if a_tag else ""
                href = a_tag.get("href", "") if a_tag else ""
                if href and not href.startswith("http"):
                    href = BASE_URL + "/" + href.lstrip("/")

                rank_tag = li.find("h6")
                rank = safe_text(rank_tag.get_text(strip=True)) if rank_tag else ""

                download_link = ""
                if j + 1 < len(li_list):
                    next_li = li_list[j + 1]
                    if "xz28" in next_li.get("class", []):
                        dl_a = next_li.find("a")
                        if dl_a:
                            dl_href = dl_a.get("href", "")
                            if dl_href and not dl_href.startswith("http"):
                                dl_href = BASE_URL + "/" + dl_href.lstrip("/")
                            download_link = dl_href
                        j += 1

                # 从URL中提取资源ID
                rid = ""
                m = re.search(r"list-show-(\d+)", href)
                if m:
                    rid = m.group(1)

                items.append({
                    "rank": rank,
                    "title": title,
                    "url": href,
                    "download_url": download_link,
                    "resource_id": rid,
                    "section": name,
                })
            j += 1

        all_data[name] = items
        print(f"  [{name}] 共 {len(items)} 条")
        for item in items:
            rank = f"{item['rank']}. " if item.get("rank") else ""
            print(f"    {rank}{item['title']}")

    return all_data

def parse_detail_page(url):
    """解析资源详情页，提取文件信息和下载验证码"""
    if not url:
        return {}

    try:
        resp = fetch(url)
    except Exception as e:
        print(f"    [!] 请求失败: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "lxml")
    info = {}

    # 文件信息
    info_box = soup.select_one(".xz72")
    if info_box:
        lis = info_box.select("li")
        for li in lis:
            text = li.get_text(strip=True)
            if "：" in text:
                key, value = text.split("：", 1)
                info[key] = safe_text(value)

    # 标题
    title_tag = soup.select_one(".xz25a h1")
    if title_tag:
        info["title"] = safe_text(title_tag.get_text(strip=True))

    # === 关键：提取下载验证码 (random) 和资源ID ===
    # 通过搜索 validateForm('xxxx','yyyy') 模式
    page_text = resp.text

    # 方法1: 搜索 script 中的 validateForm
    pattern = r"validateForm\s*\(\s*['\"](\d+)['\"]\s*,\s*['\"](\d+)['\"]\s*\)"
    match = re.search(pattern, page_text)
    if match:
        info["download_code"] = match.group(1)
        info["resource_id"] = match.group(2)
        print(f"    [*] 找到下载验证码: {info['download_code']}, 资源ID: {info['resource_id']}")
    else:
        # 方法2: 搜索 onclick 属性
        btn = soup.select_one("[onclick*='validateForm']")
        if btn:
            onclick = btn.get("onclick", "")
            match = re.search(pattern, onclick)
            if match:
                info["download_code"] = match.group(1)
                info["resource_id"] = match.group(2)
                print(f"    [*] 找到下载验证码(btn): {info['download_code']}, 资源ID: {info['resource_id']}")

    return info

def try_download_file(item, save_dir):
    """尝试下载文件"""
    title = item.get("title", item.get("resource_id", "unknown"))
    resource_id = item.get("resource_id", "")
    download_code = item.get("download_code", "")

    if not resource_id:
        print(f"    [!] {title}: 缺少资源ID，跳过")
        return False

    print(f"\n    [*] 开始处理: {title}")
    print(f"    [*] 资源ID: {resource_id}, 验证码: {download_code or '无'}")

    # 先访问详情页设置 downids cookie（必须）
    for _ in range(2):
        try:
            s.get(f"{BASE_URL}/list-show-{resource_id}.html", timeout=15)
            break
        except:
            time.sleep(1)

    downline = "https://storage.chinakaoyan.com/"

    # 策略1: 通过 act=down 获取页面，提取JS下载脚本
    dl_url = f"{BASE_URL}/list.html?act=down&id={resource_id}&downcode={download_code}&downline={downline}" if download_code else \
             f"{BASE_URL}/list.html?act=down&id={resource_id}&downline={downline}"
    print(f"    [策略1] 通过下载页面获取JS脚本...")
    try:
        resp = s.get(dl_url, timeout=30, allow_redirects=True)

        # 不需登录
        if "尚未登录" in resp.text[:500] or "请登录" in resp.text[:500]:
            print(f"    [策略1] [-] 需要登录，跳过")
        else:
            # 提取 JS 脚本 URL: js.php?act=downnotice
            m = re.search(r'js\.php\?act=downnotice[^\s"\'<>]+', resp.text)
            if m:
                js_url = BASE_URL + "/" + m.group(0).lstrip("/")
                print(f"    [策略1] [*] 找到JS脚本: {js_url}")
                return download_via_js(js_url, title, save_dir)
            else:
                print(f"    [策略1] [-] 未找到JS脚本")
    except Exception as e:
        print(f"    [策略1] [!] 异常: {e}")

    # 策略2: 直接构造 JS URL（不经过下载页面）
    print(f"    [策略2] 直接请求JS脚本...")
    js_url = f"{BASE_URL}/js.php?act=downnotice&id={resource_id}&downline={downline}"
    if download_via_js(js_url, title, save_dir):
        return True

    # 策略3: 尝试 http 版本的 downline
    print(f"    [策略3] 尝试 http downline...")
    js_url = f"{BASE_URL}/js.php?act=downnotice&id={resource_id}&downline=http://storage.chinakaoyan.com/"
    if download_via_js(js_url, title, save_dir):
        return True

    print(f"    [-] 所有策略均失败: {title}")
    return False


def download_via_js(js_url, title, save_dir):
    """通过JS脚本获取实际下载链接并下载文件"""
    try:
        resp = s.get(js_url, timeout=30)
        text = resp.text

        # 检查价格信息
        price_match = re.search(r'(\d+)\s*个考试币', text)
        balance_match = re.search(r'拥有[：:]\s*<h6>\s*(\d+)\s*</h6>\s*个考试币', text)
        if price_match:
            price = price_match.group(1)
            balance = balance_match.group(1) if balance_match else "?"
            if price != "0":
                print(f"    [*] 本资源需要 {price} 考试币，当前余额: {balance}")
                print(f"    [-] 考试币不足，跳过下载")
                return False

        # 从JS中提取 storage 下载URL
        m = re.search(r'https?://storage\.chinakaoyan\.com/getdown\.php[^\s"\'<>]*', text)
        if not m:
            # 也可能是其他存储URL模式
            m = re.search(r'https?://storage\.chinakaoyan\.com/[^\s"\'<>]+', text)

        if not m:
            print(f"    [*] JS中未找到存储URL")
            # 保存JS以便调试
            js_debug = os.path.join(save_dir, f"js_debug_{title[:20]}.js")
            with open(js_debug, "w", encoding="utf-8") as f:
                f.write(text)
            return False

        file_url = m.group(0)
        print(f"    [*] 获取到存储URL: {file_url}")

        # 下载文件
        return download_from_url(file_url, title, save_dir)

    except Exception as e:
        print(f"    [!] JS请求失败: {e}")
        return False


def extract_file_url(text):
    """从HTML中提取存储服务器上的文件URL"""
    patterns = [
        r'https?://storage\.chinakaoyan\.com/[^\s"\'<>]+',
        r'https?://[^\s"\'<>]*\.chinakaoyan\.com/[^\s"\'<>]+(?:\.pdf|\.rar|\.zip|\.doc|\.docx)',
        r'https?://[^\s"\'<>]*\.chinakaoyan\.com/[^\s"\'<>]*file[^\s"\'<>]*',
    ]
    for p in patterns:
        urls = re.findall(p, text)
        if urls:
            return urls[0]
    return None

def download_from_url(file_url, title, save_dir):
    """从指定URL下载文件（带storage必要的请求头）"""
    try:
        storage_headers = {
            "Referer": f"{BASE_URL}/",
        }
        resp = s.get(file_url, timeout=60, stream=True, headers=storage_headers)
        content_type = resp.headers.get("Content-Type", "")

        if resp.status_code == 403:
            print(f"    [!] 存储服务器返回403，可能缺少认证cookie")
            return False

        if "text/html" in content_type:
            # 检查是否是余额不足
            if "余额不够" in resp.text or "充值" in resp.text:
                print(f"    [!] 考试币不足，需要充值才能下载")
            elif "尚未登录" in resp.text:
                print(f"    [!] 需要登录才能下载")
            else:
                print(f"    [!] 存储服务器返回了HTML而非文件，下载失败")
            return False

        return save_file(resp.content, title, content_type, save_dir, resp.headers)
    except Exception as e:
        print(f"    [!] URL下载失败: {e}")
        return False

def save_file(content, title, content_type, save_dir, resp_headers=None):
    """保存文件到磁盘"""
    # 确定扩展名
    ext_map = {
        "application/pdf": ".pdf",
        "application/x-rar-compressed": ".rar",
        "application/zip": ".zip",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }

    ext = ext_map.get(content_type, "")
    if not ext and resp_headers:
        content_disposition = resp_headers.get("Content-Disposition", "")
        m = re.search(r'filename[^=]*=[\s"]*([^"]+)', content_disposition)
        if m:
            filename = m.group(1)
            ext = os.path.splitext(filename)[1] or ""

    if not ext:
        ext = ".file"

    # 清理文件名
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:80]
    filepath = os.path.join(save_dir, f"{safe_title}{ext}")

    with open(filepath, "wb") as f:
        f.write(content)

    size_mb = len(content) / 1024 / 1024
    print(f"    [+] 已保存: {filepath} ({size_mb:.1f}MB)")
    return True

def save_report(all_data):
    """保存爬取结果到JSON和TXT"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    report = {
        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": BASE_URL,
        "sections": {}
    }
    for section_name, items in all_data.items():
        report["sections"][section_name] = items

    json_path = os.path.join(DOWNLOAD_DIR, f"resources_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n[+] JSON 报告: {json_path}")

    txt_path = os.path.join(DOWNLOAD_DIR, f"resources_{timestamp}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"考研资料爬取报告 - {report['crawl_time']}\n")
        f.write(f"来源: {BASE_URL}\n")
        f.write("=" * 70 + "\n\n")
        for section_name, items in report["sections"].items():
            f.write(f"【{section_name}】({len(items)}条)\n")
            f.write("-" * 50 + "\n")
            for item in items:
                rank = f"{item['rank']}. " if item.get("rank") else ""
                f.write(f"  {rank}{item['title']}\n")
                f.write(f"    链接: {item['url']}\n")
                f.write(f"    资源ID: {item.get('resource_id', '')}\n")
                if item.get("download_code"):
                    f.write(f"    下载验证码: {item['download_code']}\n")
                f.write("\n")
    print(f"[+] TXT 报告: {txt_path}")

    return json_path

# ========== 主流程 ==========

def main():
    import sys

    print("=" * 60)
    print("考研资料全自动爬虫 - download.chinakaoyan.com")
    print("=" * 60)

    # 默认账号（手机号登录）
    DEFAULT_USERNAME = "18536100055"
    DEFAULT_PASSWORD = "Zjhzjhzjh666"

    # 1. 账号处理 - 使用默认账号
    username, password = DEFAULT_USERNAME, DEFAULT_PASSWORD
    if len(sys.argv) >= 3:
        username, password = sys.argv[1], sys.argv[2]

    print(f"\n[*] 使用账号登录: {username[:3]}****{username[-4:]}")
    logged_in, username, password = try_login(username, password)

    if logged_in:
        print(f"[+] 当前登录状态: 已登录")
    else:
        print(f"[-] 当前登录状态: 未登录（只能获取资源列表）")
        print("[-] 请检查账号密码是否正确")

    # 2. 爬取首页资源
    all_data = parse_homepage()
    if not all_data:
        print("[-] 未爬取到任何数据")
        return

    total = sum(len(items) for items in all_data.values())
    print(f"\n[*] 共找到 {total} 条资源")

    # 3. 获取每个资源的详细信息（包括下载验证码）
    print("\n" + "=" * 60)
    print("正在获取资源详情...（每个详情页间隔1秒）")
    print("=" * 60)

    for section_name, items in all_data.items():
        for item in items:
            url = item.get("url", "")
            if url:
                detail = parse_detail_page(url)
                item["file_type"] = detail.get("文件格式", "")
                item["file_size"] = detail.get("文件大小", "")
                item["upload_time"] = detail.get("上传时间", "")
                item["download_code"] = detail.get("download_code", "")
                if not item.get("resource_id") and detail.get("resource_id"):
                    item["resource_id"] = detail["resource_id"]

                print(f"    {item['title']}")
                print(f"      格式: {item['file_type']}, 大小: {item['file_size']}, 时间: {item['upload_time']}")

                time.sleep(1)  # 礼貌延迟，避免被封

    # 4. 保存报告
    save_report(all_data)

    # 5. 尝试下载（仅登录后有效）
    if logged_in:
        print("\n" + "=" * 60)
        print("开始下载文件...")
        print("=" * 60)

        # 为每个板块创建子目录
        for section_name, items in all_data.items():
            section_dir = os.path.join(DOWNLOAD_DIR, section_name)
            os.makedirs(section_dir, exist_ok=True)

            for item in items:
                if item.get("download_code") or item.get("resource_id"):
                    success = try_download_file(item, section_dir)
                    if success:
                        print(f"  [+] {item['title']} 下载成功")
                    else:
                        print(f"  [-] {item['title']} 下载失败")
                else:
                    print(f"  [-] {item['title']}: 缺少资源ID或验证码，跳过")

                time.sleep(0.5)  # 礼貌延迟

    # 6. 总结
    print("\n" + "=" * 60)
    print("执行完成！")
    print("=" * 60)
    print(f"\n结果保存在: {DOWNLOAD_DIR}/")
    print(f"共发现 {total} 条资源")

    if not logged_in:
        print("\n未登录，下载受限。解决方案:")
        print("  请检查账号密码是否正确")
        print("  用法: python pachong.py <手机号> <密码>")
    else:
        print("\n下载结果请查看上方日志")

if __name__ == "__main__":
    main()
