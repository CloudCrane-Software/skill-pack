# Higress 上游注册准备文档 —— 火山方舟（Ark）/ 豆包模型接入

> 状态：**准备文档，未执行任何注册/变更**（工单 D-04 动作 4）。
> 负责人：owner 提供 Ark API Key 后由 ops 执行；本文档不含任何密钥。
> 关联：`packs/doubao-harvest/`（豆包 SKILL 改造包；其依赖的模型服务方舟上游即本文档对象）。

## 0. 前置清单（[待owner]）

| 项 | 状态 | 说明 |
|---|---|---|
| ARK_API_KEY | [待owner] | 从火山方舟控制台「API Key 管理」创建；owner 手工提供，经密钥通道（Vault/密钥托管）交接，**禁止**进 git/对话/日志 |
| 目标模型 endpoint | [待owner] | 方舟推理接入点（ep-xxxx 形式）或模型名；按 doubao-harvest 技能所需能力（长文本/视觉）选型 |
| Higress 实例 | [待现场确认] | 目标集群/控制台地址、命名空间；本文按 Higress AI 网关标准能力写，具体 CRD 版本以现场为准 |
| 出口网络 | [待现场确认] | 网关到方舟 endpoint（`ark.cn-beijing.volces.com` 一类地域域名）的出网放行 |

## 1. 注册步骤（ops 执行时照此操作；注释为 ops 备注）

```yaml
# ops NOTE: 以下为 Higress AI 上游（LLM provider）配置草案。
# 字段名以现场 Higress 版本的 AiProxy/McpBridge 或控制台「AI 服务提供者」表单为准；
# 执行前先在测试路由灰度，勿直接切生产流量。
apiVersion: extensions.higress.io/v1alpha1
kind: LlmProvider aims: ark          # 控制台操作时对应「AI 服务提供者 → 火山方舟」
metadata:
  name: ark-doubao
spec:
  provider:
    type: volcengine                  # 火山方舟（Ark）兼容 OpenAI 协议
    token: ${ARK_API_KEY}             # ops NOTE: 从密钥托管注入，禁止明文落配置库
    # ops NOTE: 方舟走推理接入点时用 model: ep-xxxx；按需配置超时与重试
```

```bash
# ops NOTE: 密钥注入示例（K8s Secret 途径；具体以现场密钥管理约定为准）
# kubectl create secret generic ark-credential --from-literal=ARK_API_KEY='<owner 提供>'
```

## 2. 验证（注册后）

```bash
# ops NOTE: 经 Higress 网关域名发起一次最小补全，确认 200 与模型回包
# curl -sS https://<higress-gateway>/v1/chat/completions \
#   -H "Authorization: Bearer <网关侧凭据>" \
#   -H "Content-Type: application/json" \
#   -d '{"model":"<ep-xxxx>","messages":[{"role":"user","content":"只回复一个字：好"}]}'
```

- 预期：HTTP 200，`choices[0].message.content` 非空。
- 失败排查顺序：出网放行 → token 有效性（方舟控制台核对）→ endpoint 拼写 → 网关路由匹配。

## 3. 回滚

- 控制台停用/删除 `ark-doubao` provider，或 `kubectl delete` 对应 CR；路由回切原上游。
- 密钥泄露处置：方舟控制台吊销该 API Key → owner 重发 → 仅更新 Secret，不改路由。

## 4. 边界声明

- 本文只覆盖「Higress 上游注册」的准备；方舟 key 未到位前 **不得** 执行第 1-3 节（[待owner]）。
- 本文档不涉及豆包工作客户端登录态/凭据（该路径违反豆包 ToS，见 `skill-mapping.md` §4）；doubao-harvest 技能的模型调用一律走本上游或其它自建上游。
