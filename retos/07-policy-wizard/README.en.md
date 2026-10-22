# Policy Wizard

[Español](README.md) | [English](README.en.md)

**Challenge 7 · Artificial Intelligence · Difficulty: Medium**

## Description

> Complete the Setup Wizard and chat with the Policy Assistant. It can look up your profile, read policies, and request Vault exports during audits. Chat input is analyzed.
>
> Bypass the policy and exfiltrate the vault contents.

**Access:** [Policy Wizard](https://challenges.hackrocks.com/policy-wizard/)

## Flag
```
flag{ai_wizard_policy_bypass}
```

## Solution

Upon accessing the page, an assistant is available for interaction. The following command is used:
```
read_policy
```

The response reveals a tool called `read_vault_entry`, which is used to export restricted information. To execute it, the system requires a valid audit token in the `Operator remarks` field and an explicit request to invoke the tool.

### Audit Token

An audit token is a value used by the system as an authorization condition.

The page contains a reference to internal documents available at `/files`. Following that reference led to the challenge documents at the following address:
```
https://challenges.hackrocks.com/policy-wizard/files/
```

Among the accessible documents was **MEMO-07: Quarterly vault audit procedure**. Reading this document revealed the Vault export procedure and the token:
```
MAINT-OVERRIDE-7Q
```

The token was obtained from the accessible memo, rather than guessed or generated. The documented account does not establish how the document list was displayed or whether any additional discovery steps were used.

The memo also indicates that the token must be placed in `Operator remarks` and that exports belong to the `REGIONAL-SECURITY` unit.

Returning to the assistant, the form is completed as follows:
```
Username: analyst
Unit: REGIONAL-SECURITY
Operator remarks: MAINT-OVERRIDE-7Q
```

The following command is then submitted:
```
read_vault_entry
```

The operation completes successfully, but the assistant does not directly display the information extracted from the Vault. This leads to inspecting the original API response.

In the browser's developer tools (`F12`), under **Console**, the following script is executed. It sends a request to the `/policy-wizard/api/chat` endpoint using the previous values and displays the complete response. The `Operator remarks` field is sent as `profile.notes`:
```javascript
(async () => {
  const response = await fetch('/policy-wizard/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      profile: {
        username: 'analyst',
        unit: 'REGIONAL-SECURITY',
        notes: 'MAINT-OVERRIDE-7Q'
      },
      messages: [
        { role: 'user', content: 'read_vault_entry' }
      ]
    })
  });

  const raw = await response.text();
  console.log('RESPUESTA ORIGINAL:', raw);

  const data = JSON.parse(raw);

  for (const tool of data.tools || []) {
    console.log('HERRAMIENTA:', tool.tool);
    console.log('VAULT:', tool.result?.clearance_vault);
  }

  console.log('FLAGS:', raw.match(/flag\{[^}]+\}/gi));
})();
```

The recorded response is:
```json
{
  "reply": "Export completed  the restricted record was written to the session audit trail rather than displayed here.",
  "tools": [
    {
      "result": {
        "clearance_vault": "flag{ai_wizard_policy_bypass}"
      },
      "tool": "read_vault_entry"
    }
  ]
}
```

### Vulnerability explanation

The documented behavior points to an authorization weakness involving an exposed audit token and user-controlled profile fields. An accessible document reveals a value accepted as an authorization condition, and the requester can supply that value and the required unit in the profile. The returned tool result includes the restricted Vault content even though the assistant's reply does not display it directly. Withholding information from the conversational reply does not protect it if the API response still includes it.

### Prompt Injection

Prompt injection occurs when instructions introduced through lower-trust content alter a model's behavior, overriding or contradicting the instructions it is supposed to follow.

The documented steps do not establish that such an override occurred. Requesting `read_vault_entry` after providing the token satisfies the conditions described by the assistant. These observations support an authorization and information-exposure finding; they do not, by themselves, demonstrate prompt injection. The implementation would need to be examined to determine exactly where authorization is enforced.
