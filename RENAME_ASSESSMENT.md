# Renaming hermes-vision to hermes-neurovision

## Assessment

**Current Name**: hermes-vision
**Proposed Name**: hermes-neurovision

**Difficulty**: Medium (546 occurrences across 76 files)

## Why Rename?

- More descriptive: "neurovision" better describes the neural network visualization
- Distinguishes from generic "vision" (could be computer vision)
- Already called "Hermes Neurovisualizer" in docs
- Aligns with the concept better

## Files That Need Changing

### Critical (Package Structure)
1. **Directory name**: `hermes_vision/` → `hermes_neurovision/`
2. **pyproject.toml**: Package name, script entry point
3. **All Python imports**: `from hermes_vision` → `from hermes_neurovision`

### User-Facing
4. **README.md**: All occurrences
5. **CLI command**: `hermes-vision` → `hermes-neurovision`
6. **File paths**: `~/.hermes/vision/` → `~/.hermes/neurovision/`
7. **Hook path**: `~/.hermes/hooks/hermes-vision/` → `~/.hermes/hooks/hermes-neurovision/`

### Documentation
8. **All .md files**: References throughout
9. **Skill documentation**: hermes-vision-theme-design skill
10. **.hvtheme format**: Maybe keep as-is for compatibility?

### Git/GitHub
11. **Repository name**: Would need GitHub rename
12. **Tags**: v0.1.0 already tagged as hermes-vision
13. **URLs**: All links would need updating

## Risk Assessment

### Low Risk
- Python package internals (imports, module names)
- Documentation files
- Local configs/paths

### Medium Risk
- CLI command name (users would need to reinstall)
- Hook paths (existing installations would break)
- File format (.hvtheme references hermes_vision_version)

### High Risk
- Git history (but preserved with rename)
- Existing user installations (need migration)
- Community themes already exported
- Skill references in hermes-agent

## Recommended Approach

### Option 1: Rename Now (Pre-Release)
**Pros**:
- Clean start
- No legacy baggage
- v0.1.1 is first "real" release

**Cons**:
- Need to update everything
- Breaks any existing users (few if any)
- Skill needs updating

**Time**: ~2-3 hours

### Option 2: Rename Later (v0.2.0)
**Pros**:
- Get v0.1.1 out first
- Plan migration properly
- Provide backwards compatibility

**Cons**:
- More users to migrate
- More exported themes to deal with

**Time**: ~4-5 hours (with migration)

### Option 3: Keep hermes-vision
**Pros**:
- No work needed
- No breaking changes
- Already established

**Cons**:
- Less descriptive name
- Missed opportunity

## If We Rename Now (Action Items)

1. **Package Structure** (~30 min)
   ```bash
   git mv hermes_vision hermes_neurovision
   find . -type f -name "*.py" -exec sed -i 's/hermes_vision/hermes_neurovision/g' {} +
   ```

2. **Project Config** (~10 min)
   - Update pyproject.toml (name, version, scripts)
   - Update README.md
   - Update all other .md files

3. **User Paths** (~20 min)
   - Update all references to ~/.hermes/vision/ → ~/.hermes/neurovision/
   - Update hook paths
   - Update import/export code

4. **CLI Command** (~10 min)
   - Update script name in pyproject.toml
   - Update all documentation

5. **File Format** (~20 min)
   - Decision: Keep .hvtheme or change to .hvntheme?
   - Update hermes_vision_version → hermes_neurovision_version
   - Or keep as-is for compatibility

6. **Skill Update** (~30 min)
   - Update hermes-vision-theme-design skill
   - Update all references
   - Update examples

7. **Testing** (~30 min)
   - Test all commands work
   - Test import/export
   - Test paths

**Total**: ~2.5 hours

## Recommendation

**Rename now before v0.1.1 release** because:

1. We're still in dev branch
2. No real users yet (v0.1.0 was just initial)
3. Clean slate for official release
4. Better name long-term
5. Minimal migration pain now

## File Format Decision

Keep `.hvtheme` extension for compatibility, but:
- Change internal field: `hermes_neurovision_version`
- Keep backwards compatibility with `hermes_vision_version`

## Migration Checklist

- [ ] Rename directory: hermes_vision → hermes_neurovision
- [ ] Update all Python imports
- [ ] Update pyproject.toml
- [ ] Update README.md and all docs
- [ ] Update CLI command name
- [ ] Update user config paths
- [ ] Update hook paths
- [ ] Update export/import code
- [ ] Update skill documentation
- [ ] Test full workflow
- [ ] Update CHANGELOG
- [ ] Create migration guide for any existing users
