# Version Compatibility & Schema Evolution

## Overview

The .hvtheme format needs to handle version mismatches gracefully as the schema evolves.

## Version Schema

```json
{
  "format_version": "1.0",
  "metadata": {
    "hermes_vision_version": "0.1.1"
  }
}
```

- **format_version**: .hvtheme file format version (schema)
- **hermes_vision_version**: Version of Hermes Vision that created the file

## Compatibility Strategy

### Import Rules

| File Version | Import Result | Behavior |
|--------------|---------------|----------|
| 1.0 (same)   | ✓ Success     | Full support |
| 1.1 (newer minor) | ⚠ Warning | Import with defaults for new fields |
| 0.9 (older)  | ⚠ Migrate     | Attempt automatic migration |
| 2.0 (newer major) | ✗ Error   | Reject with upgrade message |

### Case 1: Newer Minor Version

User has v0.1.1, imports theme from v0.1.2 (format 1.1)

```python
if file_version.minor > current_version.minor:
    print("⚠ Theme from newer version (1.1)")
    print("  Some features may not work. Consider upgrading.\n")
    # Continue import, use defaults for unknown fields
```

### Case 2: Newer Major Version

User has v0.1.1, imports theme from v0.3.0 (format 2.0)

```python
if file_version.major > current_version.major:
    print("✗ Cannot import theme")
    print(f"  Requires format v{file_version}")
    print(f"  Current: v{current_version}")
    print("  Please upgrade Hermes Vision")
    return None
```

### Case 3: Older Version

User imports theme from pre-release (format 0.9)

```python
if file_version.major == 0:
    print("⚠ Migrating from pre-release format...\n")
    data = migrate_v0_to_v1(data)
```

## Schema Evolution Examples

### v1.0 → v1.1: Add Optional Field

```python
# v1.1 adds animation_speed
CONFIG_DEFAULTS = {
    "background_density": 0.030,
    "star_drift": 0.10,
    "animation_speed": 1.0,  # NEW in v1.1
    # ...
}

def extract_config(data):
    config = {}
    for field, default in CONFIG_DEFAULTS.items():
        config[field] = data["config"].get(field, default)
    return config
```

### v1.0 → v2.0: Rename Field

Old themes use `background_density`, new themes use `star_density`

```python
def extract_config(data):
    version = parse_version(data["format_version"])
    
    if version.major < 2:
        # Old format
        star_density = data["config"]["background_density"]
    else:
        # New format
        star_density = data["config"]["star_density"]
    
    return {"star_density": star_density, ...}
```

## Implementation

### Version Class

```python
from dataclasses import dataclass

@dataclass
class Version:
    major: int
    minor: int
    
    @classmethod
    def parse(cls, version_str: str):
        parts = version_str.split(".")
        return cls(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    
    def compatible_with(self, other) -> bool:
        """Check if this version can import from other version."""
        return self.major == other.major and self >= other
```

### Import with Version Check

```python
def import_theme(theme_path):
    with open(theme_path) as f:
        data = json.load(f)
    
    file_version = Version.parse(data.get("format_version", "0.9"))
    current_version = Version.parse("1.0")
    
    # Check major version compatibility
    if file_version.major > current_version.major:
        raise IncompatibleVersionError(
            f"Theme requires format {file_version.major}.x\n"
            f"Current version: {current_version.major}.x\n"
            f"Please upgrade Hermes Vision"
        )
    
    # Migrate old versions
    if file_version.major == 0:
        print("⚠ Migrating from pre-release format...")
        data = migrate_v0_to_v1(data)
    
    # Warn about newer minor versions
    if file_version.minor > current_version.minor:
        print(f"⚠ Theme from newer version ({file_version.major}.{file_version.minor})")
        print("  Some features may not be available\n")
    
    return _do_import(data)
```

### Export with Version

```python
def export_theme(theme_name):
    return {
        "format_version": "1.0",  # Current format version
        "metadata": {
            "hermes_vision_version": "0.1.1",  # App version
            # ...
        },
        # ...
    }
```

## Default Values Registry

```python
# All config fields with defaults
CONFIG_FIELDS = {
    # v1.0 fields
    "background_density": 0.030,
    "star_drift": 0.10,
    "node_jitter": 0.20,
    "packet_rate": 0.30,
    "packet_speed": [0.04, 0.08],
    "pulse_rate": 0.10,
    "edge_bias": 0.50,
    "cluster_count": 3,
    "palette": ["COLOR_CYAN", "COLOR_BLUE", "COLOR_WHITE", "COLOR_MAGENTA"],
    "accent_char": "*",
    
    # v1.1 fields (future)
    # "animation_speed": 1.0,
    # "glow_intensity": 0.5,
}
```

## Migration Function

```python
def migrate_v0_to_v1(data):
    """Migrate pre-release format to v1.0."""
    return {
        "format_version": "1.0",
        "metadata": {
            "name": data.get("name", "unknown"),
            "title": data.get("title", "Untitled"),
            "author": "unknown",
            "description": "Migrated from v0.9",
            "created": datetime.utcnow().isoformat() + "Z",
            "hermes_vision_version": "0.1.1"
        },
        "config": data.get("config", {}),
        "plugin": {
            "type": "custom" if "plugin_code" in data else "base",
            "code": data.get("plugin_code"),
            "class_name": data.get("plugin_class")
        }
    }
```

## Testing

```python
def test_newer_minor_version():
    """v1.1 theme into v1.0 - should work with warnings."""
    theme = {"format_version": "1.1", ...}
    result = import_theme_data(theme)
    assert result.success
    assert result.warnings  # Should warn about version mismatch

def test_newer_major_version():
    """v2.0 theme into v1.0 - should fail gracefully."""
    theme = {"format_version": "2.0", ...}
    with pytest.raises(IncompatibleVersionError):
        import_theme_data(theme)
```

## Best Practices

1. **Always backward compatible within major version**
   - v1.0 imports v1.x with defaults
   
2. **Clear error messages**
   - Show what's wrong and how to fix it
   
3. **Test with old themes**
   - Keep sample themes from each version
   
4. **Document changes**
   - Update CHANGELOG with schema changes
   
5. **Provide migration**
   - Automatic when possible
   - Clear instructions when not

## Schema Change Checklist

When evolving schema:

- [ ] Update format_version (minor vs major)
- [ ] Add defaults for new fields
- [ ] Write migration if needed
- [ ] Update import handler
- [ ] Add tests
- [ ] Document in CHANGELOG
