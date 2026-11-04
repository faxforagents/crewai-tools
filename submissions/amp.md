# CrewAI AMP submission

Prepared on 2026-11-04. Nothing has been published.

The product is Fax for Agents. The requested scaffold name was `faxforagents`.
The distribution is `faxforagents-crewai`, version `0.1.0`.
Python imports use `faxforagents_crewai`.
The planned source repository is `https://github.com/faxforagents/crewai-tools`.

## Scaffold check

The [AMP guide](https://docs-platform.crewai.com/platform/en/guides/tool-repository) was fetched on 2026-11-04.
It documents tool creation and public publication through the CrewAI CLI.

CrewAI 1.15.35 was installed in `.coding-agent/tmp/cli-venv`.
The following command was tried with isolated, empty CLI settings.

```bash
crewai tool create faxforagents
```

It exited with code 1 and requested AMP sign-in before creating files.
It also reported that `crewai create tool` replaces the deprecated command.
No sign-in was attempted.

The package layout was built manually from that release's installed `crewai_cli/templates/tool` directory.
It retains the `src` layout, `tool.py`, exported classes, and `[tool.crewai] type = "tool"` metadata.
The [current BaseTool guide](https://docs.crewai.com/en/learn/create-custom-tools) was fetched on the same date.
The implementation uses `crewai.tools.BaseTool` and Pydantic argument schemas.

The distribution cannot also be named `faxforagents`, because it depends on the SDK with that name.
CrewAI's publisher takes the AMP handle from `project.name`.
This package therefore requests `faxforagents-crewai` at publication.
Use the handle returned by AMP for installation.

```text
pyproject.toml
README.md
LICENSE
CHANGELOG.md
src/faxforagents_crewai/__init__.py
src/faxforagents_crewai/tool.py
src/faxforagents_crewai/toolkit.py
src/faxforagents_crewai/schemas.py
src/faxforagents_crewai/_guide.py
src/faxforagents_crewai/tool-definitions.json
src/faxforagents_crewai/py.typed
tests/test_tool.py
tests/test_example.py
examples/fax_crew.py
submissions/amp.md
```

## Setup

Use Python 3.10 to 3.13, Git, and uv 0.5.0 or later.
Run `uv sync` from this checkout.
The declared dependencies include bounded versions of `crewai`, `crewai-tools`, `faxforagents`, and `pydantic`.
CrewAI and crewai-tools are constrained to `>=1.15.35,<1.16`.
The SDK is constrained to `>=0.2.3,<0.3`.

Create a sandbox credential in the [Fax for Agents dashboard](https://app.faxforagents.com/).
Store it as `FAXFORAGENTS_API_KEY` through host secret settings.
Use an `ffa_test_` credential. Sandbox is enabled by default.
The SDK contacts `https://api.faxforagents.com`.
Document contents and destinations are sent there for processing.
Received documents and extracted text are returned as untrusted data.

## Billing

The [pricing page](https://faxforagents.com/pricing/) was fetched on 2026-11-04.
Its rate table identifies `launch-v2`, effective 2026-10-31.
Some introductory text still mentions 2026-10-28.
The listed US and Canada prices are below, in USD.

| Item | Price |
|---|---|
| Sandbox | Free |
| Sent page | $0.039 per delivered page |
| Received page | $0.019 per page |
| Fax number | $2 monthly |
| Minimum wallet top-up | $10 |
| Optional Agent workspace | $19 monthly |

Live sends spend a prepaid wallet. A subscription is optional.
Cover pages count as billable pages. International destinations use separate rates.
Failed sends are uncharged. Partial delivery charges confirmed pages.
Unknown outcomes retain the hold until review.
Use `get_fax_capabilities` and `quote_fax` for current routes and exact prices.
OCR and structured extraction can incur separate charges.
Model provider charges are separate from fax charges.

## Sandbox review

Run the local checks before configuring a credential.

```bash
uv run pytest -q
uv run ruff check src tests examples
uv run mypy --python-version 3.12 src
uv build
```

The tests use fake clients and mock HTTP. The CrewAI example test uses scripted model replies.

1. Configure an `ffa_test_` credential through secret settings.
2. Run the README quickstart with a persisted operation ID.
3. Confirm preparation and quoting return `ok=true` for `+15550000001`.
4. Confirm the quote uses sandbox pricing and no fax was sent.
5. Retry with the same operation ID and unchanged payload.
6. Inspect the returned document and quote before any separate sandbox send test.

Only `send_approved_fax` can send. It requires a quote and caller idempotency key.
An optional sandbox send to `+15550000001` never reaches a carrier.
Poll `get_fax_status` until a terminal state appears.
Sandbox approval requirements still come from the API.
Never infer delivery from a queued result.

The tests verify live credential refusal in sandbox mode.
They also verify live sends cannot reach the SDK without an approval ID.
No live sends or authenticated service checks were performed during package preparation.

## Ben's publication steps

Ben must sign in to AMP and obtain publishing permission for the intended organization.
Ben must review and commit the package through the repository's normal gates.
The current publisher also requires local and remote Git state to match.
Repository creation and remote setup remain separate operator tasks.

After those gates, these are the publication commands from the package directory.

```bash
uv run crewai login
uv run crewai org list
read -r -p 'Authorized AMP organization ID: ' AMP_ORG_ID
uv run crewai org switch "$AMP_ORG_ID"
uv run crewai tool publish --public
```

No `--force` flag is needed or recommended.
Review security-check results under `CrewAI AMP > Tools > Your Tool > Versions`.
Wait for those checks to pass before installation testing.
The plain CLI command is `crewai tool publish --public`.

In a separate consumer project, install the returned handle.
If AMP assigns the requested handle, run these commands.

```bash
crewai tool install faxforagents-crewai
crewai uv sync
```

Use `crewai uv` for later dependency operations after AMP installation.
Confirm the tools import from `faxforagents_crewai` and repeat the sandbox review.
Do not install the SDK's `faxforagents` name as this AMP wrapper.

## Earlier implementation

The [upstream branch](https://github.com/bensynapse/crewAI/tree/feat/faxforagents-tool) was fetched on 2026-11-04.
The reviewed commit is `4ad18ef0a64ee06e82a74ef00962c7c6e2f8e689`.
Its document preparation, quote ordering, approval requirement, and delivery evidence behavior informed this package.
Its fake API tests were adapted to fake SDK resources and separate tool calls.
The partial, unknown, failed, and approval refusal cases remain covered.

The combined send workflow was split into canonical tools.
Resuming a send now uses the original quote ID.
Caller keys replace generated UUIDs. SDK clients replace direct HTTP requests.
The LangChain package supplied current schemas, error handling, untrusted marking, and SDK test fixtures.
The separate upstream contribution route remains outside this AMP submission.
