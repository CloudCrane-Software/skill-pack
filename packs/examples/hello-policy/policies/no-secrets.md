# 策略：输出不得含密钥（no-secrets-in-outputs）

- **范围**：本 pack 注入的所有 harness 会话的最终输出、日志、错误信息。
- **规则**：任何凭据（token / key / password / 连接串）不得以值的形式出现在输出中。
  引用形式：字段名 + 长度 + HTTP 状态码（如 `token_len=40, http=401`）。
- **违规处置**：拦截输出并记录 GuardrailRun 事件；同一会话二次违规熔断该会话。

> synthetic：本策略为格式演示而写，非提炼自任何厂商真软件。
