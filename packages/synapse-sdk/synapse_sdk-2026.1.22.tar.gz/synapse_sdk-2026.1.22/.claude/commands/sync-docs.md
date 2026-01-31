---
name: sync-docs
description: Analyze code changes and automatically sync documentation using doc-sync rules
---

Analyze code changes against documentation and automatically update docs to fix sync issues.

**Arguments:**
- `--base <ref>`: Base git reference for comparison (optional, defaults to "origin/main")
- `--auto-fix`: Automatically apply fixes to documentation (optional, defaults to false - preview only)
- `--severity <level>`: Minimum severity level to process (error/warning/info, defaults to "warning")
- `--lang <language>`: Language for output messages (ko/en, defaults to "ko")

**Usage Examples:**
- `/sync-docs` - Preview doc sync issues against origin/main
- `/sync-docs --auto-fix` - Auto-fix warning+ severity issues
- `/sync-docs --base origin/develop --severity error` - Check only errors against develop branch
- `/sync-docs --auto-fix --severity info --lang en` - Fix all issues with English output

**Process Flow:**

## 1. Check for Uncommitted Changes

IMPORTANT: This tool only analyzes **committed changes**. Before running analysis:

```bash
# Check for uncommitted changes
git status --short
```

If there are uncommitted Python files:
- **Option A (Recommended)**: Commit your changes first
  ```bash
  git add .
  git commit -m "your message"
  ```
- **Option B**: Stash, create temp commit, analyze, then restore
  ```bash
  git stash
  # Create temp commit on analysis branch
  git checkout -b temp-analysis
  git add -A
  git commit -m "temp: for doc analysis"
  # Run analysis
  # Then cleanup
  git checkout -
  git branch -D temp-analysis
  git stash pop
  ```

If uncommitted changes are found, inform the user with:

**Korean:**
```
⚠️ 커밋되지 않은 변경사항 발견

다음 파일들이 커밋되지 않았습니다:
- {file1}
- {file2}

문서 동기화 도구는 커밋된 변경사항만 분석합니다.
아래 옵션 중 선택하세요:

1. 변경사항을 커밋한 후 다시 실행: git commit -am "message" && /sync-docs
2. 계속 진행 (커밋된 변경사항만 분석)
```

**English:**
```
⚠️ Uncommitted Changes Detected

The following files have uncommitted changes:
- {file1}
- {file2}

This tool only analyzes committed changes.
Please choose:

1. Commit changes first, then re-run: git commit -am "message" && /sync-docs
2. Continue anyway (analyze committed changes only)
```

## 2. Analyze Code Changes

Run the analysis script to detect code changes:
```bash
PYTHONPATH=. uv run python scripts/doc_sync/analyze.py \
  --base <BASE_REF> \
  --head HEAD \
  --output analysis.json
```

## 3. Apply Documentation Rules

Apply doc-sync rules to find issues:
```bash
PYTHONPATH=. uv run python scripts/doc_sync/apply_rules.py \
  --input analysis.json \
  --output issues.json \
  --rules .github/doc-sync-rules.yaml
```

## 4. Display Issue Summary

Parse and display issues by severity in the selected language:

**Korean Format:**
```
📋 문서 동기화 분석 결과

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
통계:
  🔴 ERROR:   {error_count}개
  🟡 WARNING: {warning_count}개
  🔵 INFO:    {info_count}개
  📊 총:      {total}개
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

발견된 이슈:
{file_path}:
  [{SEVERITY}] {rule_label}: {element_name} (L{line})
  설명: {description}
  권장 조치: {suggestion}
```

**English Format:**
```
📋 Documentation Sync Analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary:
  🔴 ERROR:   {error_count}
  🟡 WARNING: {warning_count}
  🔵 INFO:    {info_count}
  📊 Total:   {total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues Found:
{file_path}:
  [{SEVERITY}] {rule_label}: {element_name} (L{line})
  Description: {description}
  Recommended Action: {suggestion}
```

## 5. Apply Fixes (if --auto-fix enabled)

For each issue that meets the severity threshold:

### 5.1 Docstring Issues (missing_docstring)
- Read the code file to understand function/class signature
- Generate Google-style docstring with Args, Returns, Raises sections
- Use Edit tool to add docstring to the code file
- Report fix in selected language

### 5.2 Signature Mismatch (stale_signature, breaking_signature_change)
- Read both code file and documentation file
- Extract current signature from code
- Use Edit tool to update documentation with new signature
- Update usage examples if present
- Report fix in selected language

### 5.3 Removed API Reference (removed_api_reference)
- Read documentation file
- Add deprecation notice or remove reference
- Suggest migration path if applicable
- Report fix in selected language

### 5.4 Missing New API Documentation (missing_new_api_doc)
- Read code to understand new API
- Identify appropriate documentation location using doc-sync-mapping.yaml
- Use Edit/Write tool to add API reference
- Report fix in selected language

## 6. Generate Final Report

Create a summary in the selected language:

**Korean:**
```
✅ 문서 동기화 완료

처리된 이슈: {fixed_count}/{total_issues}
- 🔴 ERROR 수정: {error_fixed}
- 🟡 WARNING 수정: {warning_fixed}
- 🔵 INFO 수정: {info_fixed}

건너뛴 이슈: {skipped_count} (심각도 기준: {severity_threshold})

수정된 파일:
- {file1}
- {file2}
...

다음 단계:
1. 변경사항 검토: git diff
2. 테스트 실행: make test
3. 문서 빌드 확인: make docs-build
4. 커밋 생성: git add . && git commit -m "docs: sync documentation with code changes"
```

**English:**
```
✅ Documentation Sync Complete

Issues Processed: {fixed_count}/{total_issues}
- 🔴 ERROR fixed: {error_fixed}
- 🟡 WARNING fixed: {warning_fixed}
- 🔵 INFO fixed: {info_fixed}

Issues Skipped: {skipped_count} (severity threshold: {severity_threshold})

Modified Files:
- {file1}
- {file2}
...

Next Steps:
1. Review changes: git diff
2. Run tests: make test
3. Verify docs build: make docs-build
4. Create commit: git add . && git commit -m "docs: sync documentation with code changes"
```

## Important Notes

**Language Selection:**
- All output messages, summaries, and reports should be in the selected language
- Code comments and docstrings should ALWAYS be in English (per project rules)
- Documentation content language should match the original file language

**Safety Checks:**
1. Never modify files without showing preview first (unless --auto-fix is explicitly set)
2. Only process issues at or above the specified severity threshold
3. Always validate syntax before writing changes
4. Create backup suggestions for manual review if auto-fix fails

**Error Handling:**
1. If analysis.json is empty, report "No code changes detected"
2. If issues.json is empty, report "No documentation sync issues found"
3. If auto-fix fails for any issue, report error and continue with next issue
4. Collect all errors and show summary at the end

**File Safety:**
- Use Edit tool for existing files (safer than Write)
- Always read file content before making changes
- Preserve file formatting and style
- Never remove content that isn't explicitly identified as problematic

**Configuration Files Used:**
- Rules: `.github/doc-sync-rules.yaml`
- Mapping: `.github/doc-sync-mapping.yaml`
- Both files are already configured and should not be modified by this command
