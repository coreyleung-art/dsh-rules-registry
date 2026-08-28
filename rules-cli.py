#!/usr/bin/env python3
"""rules-cli.py — 规则账本治理 CLI（跨平台）
用法:
  rules-cli.py list                     # 列出全部规则
  rules-cli.py get <id>                 # 查单条
  rules-cli.py add <id> <name> <category> <summary>   # 新增（status=pending 待审核）
  rules-cli.py approve <id>             # 总线审核通过 → enforced
  rules-cli.py reject <id> <reason>     # 总线拒绝 → rejected
  rules-cli.py update <id> <field> <value>  # 更新字段
  rules-cli.py sync                     # 同步到黑板（data/rules/）+ 生成全量快照
  rules-cli.py audit                    # 审计（enforced/pending/rejected 统计）
"""
import json, os, sys, time, urllib.request

RULES_FILE = os.path.expanduser("~/.dsh/rules-registry/rules.json")
# 兼容本机路径（开发期）
if not os.path.exists(RULES_FILE):
    alt = os.path.expanduser("~/dsh-collab/rules-registry/rules.json")
    if os.path.exists(alt):
        RULES_FILE = alt

BB = "http://127.0.0.1:8792"

def load():
    with open(RULES_FILE) as f:
        return json.load(f)

def save(data):
    data["lastUpdated"] = time.strftime("%Y-%m-%d")
    with open(RULES_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_rule(data, rid):
    for r in data["rules"]:
        if r["id"] == rid:
            return r
    return None

def cmd_list(data):
    print(f"规则账本 v{data['version']} | {data['audit']['ruleCount']} 条 | enforced {data['audit']['enforced']}")
    print("-" * 90)
    for r in data["rules"]:
        status = {"enforced": "✅", "pending": "⏳", "rejected": "❌"}.get(r["status"], r["status"])
        print(f"  {r['id']} {status} [{r['category']}] {r['name']}")
        print(f"      {r['summary'][:70]}")

def cmd_get(data, rid):
    r = find_rule(data, rid)
    if not r:
        print(f"❌ 规则 {rid} 不存在")
        return
    print(json.dumps(r, ensure_ascii=False, indent=2))

def cmd_add(data, rid, name, category, summary):
    if find_rule(data, rid):
        print(f"❌ 规则 {rid} 已存在")
        return
    rule = {
        "id": rid, "name": name, "category": category, "scope": "all-bus-devices",
        "status": "pending", "version": "1.0",
        "source": "rules-registry/rules.json",
        "summary": summary, "detail": "",
        "enforcedBy": "process", "added": time.strftime("%Y-%m-%d"), "approvedBy": None,
    }
    data["rules"].append(rule)
    data["audit"]["ruleCount"] += 1
    save(data)
    print(f"✅ 规则 {rid} 已提交（status=pending，待总线审核）")

def cmd_approve(data, rid):
    r = find_rule(data, rid)
    if not r:
        print(f"❌ 规则 {rid} 不存在"); return
    r["status"] = "enforced"
    r["approvedBy"] = "bus"
    r["approvedAt"] = time.strftime("%Y-%m-%d %H:%M")
    data["audit"]["enforced"] = sum(1 for x in data["rules"] if x["status"] == "enforced")
    save(data)
    print(f"✅ 规则 {rid} 已批准 → enforced（同步泛化所有侧后生效）")

def cmd_reject(data, rid, reason):
    r = find_rule(data, rid)
    if not r:
        print(f"❌ 规则 {rid} 不存在"); return
    r["status"] = "rejected"
    r["rejectReason"] = reason
    save(data)
    print(f"❌ 规则 {rid} 已拒绝: {reason}")

def cmd_update(data, rid, field, value):
    r = find_rule(data, rid)
    if not r:
        print(f"❌ 规则 {rid} 不存在"); return
    if field in r:
        r[field] = value
        save(data)
        print(f"✅ 规则 {rid}.{field} = {value}")
    else:
        print(f"❌ 字段 {field} 不存在")

def cmd_sync(data):
    """同步到黑板（data/rules/）+ 生成全量快照"""
    # 全量快照
    snap = json.dumps(data, ensure_ascii=False)
    # 黑板同步
    try:
        req = urllib.request.Request(
            f"{BB}/data/rules/registry-v{data['version'].replace('.', '-')}",
            data=snap.encode(), method="PUT",
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"✅ 已同步黑板: HTTP {resp.status}")
    except Exception as e:
        print(f"⚠️ 黑板同步失败: {e}")
    # 生成快照文件
    snap_file = os.path.join(os.path.dirname(RULES_FILE), f"rules-v{data['version']}.snapshot.json")
    with open(snap_file, "w") as f:
        f.write(snap)
    print(f"✅ 快照: {snap_file}")
    # 生成规则本 md（人类可读，端侧同步用）
    md = ["# 规则账本（完整规则本）", "", f"> v{data['version']} | {data['audit']['ruleCount']} 条 | 所有总线设备必须服从", ""]
    for r in data["rules"]:
        st = {"enforced": "✅", "pending": "⏳", "rejected": "❌"}.get(r["status"], r["status"])
        md.append(f"## {r['id']} {st} {r['name']}")
        md.append(f"- 分类: {r['category']} | 范围: {r['scope']} | 状态: {r['status']}")
        md.append(f"- 摘要: {r['summary']}")
        if r.get("detail"): md.append(f"- 详情: {r['detail']}")
        md.append("")
    md_file = os.path.join(os.path.dirname(RULES_FILE), "RULES.md")
    with open(md_file, "w") as f:
        f.write("\n".join(md))
    print(f"✅ 规则本: {md_file}")

def cmd_audit(data):
    from collections import Counter
    c = Counter(r["status"] for r in data["rules"])
    print(f"规则总数: {len(data['rules'])}")
    for k, v in c.items():
        print(f"  {k}: {v}")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    data = load()
    cmd = args[0]
    if cmd == "list": cmd_list(data)
    elif cmd == "get" and len(args) > 1: cmd_get(data, args[1])
    elif cmd == "add" and len(args) > 4: cmd_add(data, args[1], args[2], args[3], args[4])
    elif cmd == "approve" and len(args) > 1: cmd_approve(data, args[1])
    elif cmd == "reject" and len(args) > 2: cmd_reject(data, args[1], args[2])
    elif cmd == "update" and len(args) > 3: cmd_update(data, args[1], args[2], args[3])
    elif cmd == "sync": cmd_sync(data)
    elif cmd == "audit": cmd_audit(data)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
