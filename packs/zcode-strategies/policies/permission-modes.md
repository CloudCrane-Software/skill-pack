<!-- distill: vendor/zcode.cjs permission-mode schema, string offset 1366030; ExitPlanMode allowedPrompts from the plan-mode tool surface -->

# Permission modes

`permissionMode` selects how much the agent may do before a person approves. The harness enforces the mode. This document states the semantics a strategy pack assumes.

| Mode | What the agent may do | When to pause |
| --- | --- | --- |
| `build` | Prepare edits and commands, then stop before they land | Pause before each change and wait for approval |
| `edit` | Apply file edits as they are produced | Pause for commands and other non-edit side effects |
| `plan` | Read, search, and write a plan | No writes and no mutating commands; the workspace stays read-only |
| `yolo` | Proceed through edits and commands without a per-step stop | Default is full auto; still refuse the security boundary in the identity fragment |

## What may pass without a prompt

Low-risk reads can proceed in every mode: opening a file, searching, listing, and fetching public documentation. They do not change the tree or the machine.

## What always needs approval outside `yolo`

High-risk actions need an explicit allow even when the surrounding mode is permissive about ordinary edits:

- deleting or moving files, or rewriting a large surface
- network calls that send credentials or mutate a remote service
- git history rewrites, force pushes, and publishing
- installing packages or changing shared permissions

`build` treats every change as high-risk: it pauses and waits. `edit` auto-applies edits and still pauses for the list above. `plan` does not reach those actions at all.

## `allowedPrompts` on leaving plan mode

`ExitPlanMode` carries two things: the plan, and `allowedPrompts`.

Each prompt describes a category of action the execution phase may take, such as "run the project test suite" or "edit source under the package being changed". It does not embed a concrete command line, a flag set, or a shell one-liner. The execution phase still goes through the permission mode that is active then. A category allow is not a blank check for a different action.
