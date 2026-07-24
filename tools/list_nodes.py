"""用 OAuth token 递归获取知识库所有节点"""
import json, httpx

SPACE_ID = "7589642043471924447"

with open("C:/Users/a1867/.feishu-docx/token.json") as f:
    token_data = json.load(f)

access_token = token_data["access_token"]
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

def get_children(parent_token=None):
    """获取某节点的子节点列表"""
    url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{SPACE_ID}/nodes"
    params = {"page_size": 50}
    if parent_token:
        params["parent_node_token"] = parent_token
    resp = httpx.get(url, headers=headers, params=params, timeout=30)
    data = resp.json()
    if data.get("code") != 0:
        print(f"  API error: {data}")
        return []
    return data.get("data", {}).get("items", [])

def walk_tree(token=None, depth=0):
    """递归遍历节点树"""
    indent = "  " * depth
    results = []
    nodes = get_children(token)
    for node in nodes:
        title = node.get("title", "??")
        node_token = node.get("node_token", "")
        obj_type = node.get("obj_type", "")
        has_child = node.get("has_child", False)
        obj_token = node.get("obj_token", "")

        print(f"{indent}[{obj_type}] {title}")

        if obj_type in ("doc", "docx") and obj_token:
            doc_url = f"https://zihao-ai.feishu.cn/wiki/{obj_token}"
            results.append((title, doc_url))
        if obj_type == "folder" or has_child:
            if has_child:
                results.extend(walk_tree(node_token, depth + 1))

    return results

# 获取顶级节点
print("获取根节点列表...")
root_nodes = get_children()
print(f"根节点数: {len(root_nodes)}")
for n in root_nodes:
    print(f"  [{n.get('obj_type')}] {n.get('title')}")

# 递归获取所有页面
print("\n递归遍历...")
all_pages = walk_tree(None)
print(f"\n共找到 {len(all_pages)} 个文档页面")

with open("D:/projects/so100-arm-lerobot/子豪兄项目/pages.txt", "w", encoding="utf-8") as f:
    for title, url in all_pages:
        f.write(f"{title}\t{url}\n")

print("已保存到 pages.txt")
