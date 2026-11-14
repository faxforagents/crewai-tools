# Changelog

## Unreleased

The SDK dependency is `faxforagents>=0.2.3,<0.7`. The range ended below 0.3 and shut out the current SDK.
The tests pass against SDK 0.2.3, 0.5.0 and 0.6.0. No tool changed.
The README says the hosted MCP server has two card tools this package does not have.

## 0.1.0, 2026-11-04

Prepared the first CrewAI AMP package. Publication is pending.

- Added 15 canonical tools with Pydantic input schemas.
- Required caller idempotency keys for mutations and approval IDs for live sends.
- Added sandbox credential checks and untrusted result marking.
- Added fake SDK tests, an offline CrewAI example test, and AMP submission instructions.

The implementation adapts the earlier CrewAI branch and the LangChain package's current SDK boundaries.
