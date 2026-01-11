# Code Simplification Plan: GUI Files

## Overview
This plan identifies optimization opportunities for `windows_sleep_gui.pyw` and `linux_sleep_gui.pyw` to reduce duplication, improve maintainability, and prepare for potential unified GUI implementation.

---

## 1. Code Duplication Opportunities

### 1.A ToolTip Class (High Priority)
Both files contain nearly identical `ToolTip` classes with minor differences:
- Windows version uses `show_tip`/`hide_tip` method names
- Linux version uses `on_enter`/`on_leave` method names
- Both use identical positioning and styling logic

**Recommendation**: Extract `ToolTip` to a shared module (e.g., `gui_helpers.py`). This class is purely UI-related and has no platform-specific dependencies.

**Action**:
- [ ] Create `gui_helpers.py`
- [ ] Move `ToolTip` class to shared module
- [ ] Update both GUI files to import from `gui_helpers`

---

### 1.B Sleep Loop Logic (High Priority)
The countdown and cycling logic in `sleep_loop()` (Windows, lines 102-161) and `sleep_mode_thread()` (Linux, lines 247-321) share approximately 80% identical structure:
- Same countdown loop with `for remaining in range(seconds, 0, -1)`
- Identical progress calculation: `((total_seconds - remaining) / total_seconds) * 100`
- Same time formatting: `divmod(remaining, 60)` followed by `f"{mins:02d}:{secs:02d}"`
- Same cycling logic pattern
- Same status update patterns for each phase

**Recommendation**: Extract the core countdown timer logic into a shared utility. The platform-specific parts (executing sleep commands) can be passed as callbacks.

**Action**:
- [ ] Create `countdown_timer()` function in `gui_helpers.py`
- [ ] Refactor both `sleep_loop()` and `sleep_mode_thread()` to use shared function
- [ ] Pass sleep execution as a callback parameter

---

### 1.C UI Reset Pattern (Medium Priority)
Both GUIs have identical patterns for resetting UI after operations:
- Re-enabling start button
- Disabling cancel button
- Re-enabling entry fields
- Resetting progress bar to 0

This pattern appears multiple times in each file.

**Recommendation**: Extract to a shared function like `reset_ui_to_idle()`.

**Action**:
- [ ] Create `reset_ui_to_idle()` function in `gui_helpers.py`
- [ ] Replace all UI reset patterns with function call
- [ ] Accept button/entry widget references as parameters

---

### 1.D Input Validation (Medium Priority)
Both files have the same validation pattern:
```python
try:
    minutes = int(entry.get())
    if minutes < 0:
        raise ValueError
except ValueError:
    messagebox.showerror("Invalid Input", "Please enter a non-negative integer.")
    return
```

**Recommendation**: Create a shared `validate_positive_integer()` function.

**Action**:
- [ ] Create `validate_positive_integer(value_str, field_name)` in `gui_helpers.py`
- [ ] Replace validation code in both files

---

## 2. Functions to Extract and Share

### 2.A Time Formatting Utility
`divmod(remaining, 60)` followed by `f"{mins:02d}:{secs:02d}"` appears in both files.

**Recommendation**: Create `format_countdown(seconds: int) -> str` function.

**Function Signature**:
```python
def format_countdown(seconds: int) -> str:
    """Format seconds as MM:SS string."""
    mins, secs = divmod(seconds, 60)
    return f"{mins:02d}:{secs:02d}"
```

**Action**:
- [ ] Add to `gui_helpers.py`
- [ ] Replace both occurrences with function call

---

### 2.B Progress Calculation
The formula `((total_seconds - remaining) / total_seconds) * 100` is duplicated.

**Recommendation**: Create `calculate_progress(elapsed: int, total: int) -> float` function.

**Function Signature**:
```python
def calculate_progress(elapsed: int, total: int) -> float:
    """Calculate progress percentage (0-100)."""
    if total == 0:
        return 0.0
    return (elapsed / total) * 100
```

**Action**:
- [ ] Add to `gui_helpers.py`
- [ ] Replace both occurrences with function call

---

### 2.C Confirmation Dialog Builder
Both GUIs construct confirmation messages with cycling status.

**Recommendation**: Create `build_confirm_message(minutes, enable_cycling, operation_type)` helper.

**Action**:
- [ ] Create helper in `gui_helpers.py`
- [ ] Centralize confirmation message logic

---

### 2.D Settings Window Pattern
Both `open_settings()` functions follow the same structure. The Linux version has additional sections, but the base pattern is identical.

**Recommendation**: Create shared components for cycling options, about section, save/cancel buttons. Platform-specific sections added conditionally.

**Action**:
- [ ] Extract shared settings sections
- [ ] Create builder functions for reusable components
- [ ] Reduce `open_settings()` complexity

---

## 3. Clarity and Maintainability Improvements

### 3.A Global State Management (High Priority)
Both files use multiple global variables for state:
- Windows: `stop_timer`, `current_thread`, `initial_minutes`, `enable_cycling`, `wait_minutes_setting`
- Linux: `current_mode`, `current_sleep_type`, `stop_operation`, `prevent_process`, `enable_cycling`, `wait_minutes_setting`, `force_ignore_inhibitors`, `logger`

**Recommendation**: Consider encapsulating state in a simple dataclass. This would make it clearer what state the application tracks and reduce potential bugs from global variable misuse.

**Action**:
- [ ] Create `GUIState` dataclass with all state variables
- [ ] Replace global variables with state object
- [ ] Update all functions to pass state as parameter (optional but recommended)

---

### 3.B Inconsistent Naming (Medium Priority)
- Windows uses `stop_timer` while Linux uses `stop_operation`
- Windows uses `current_thread` while Linux does not track the thread reference
- Windows uses `initial_minutes` parameter naming, Linux uses `initial_minutes_param` in one place

**Recommendation**: Standardize naming across both files for consistency.

**Action**:
- [ ] Rename Windows `stop_timer` → `stop_operation`
- [ ] Add consistent `current_thread` tracking to Linux
- [ ] Standardize parameter naming conventions

---

### 3.C Mixed Module-Level Code and Functions (Medium Priority)
Both files have module-level code (widget creation, event binding) scattered after function definitions.

**Recommendation**: Reorganize to follow a clear structure:
1. Imports
2. Constants/Config loading
3. Class definitions (ToolTip)
4. Function definitions
5. Main entry point containing all widget creation

**Action**:
- [ ] Reorganize both files to follow consistent structure
- [ ] Move all widget creation to `if __name__ == "__main__":` block

---

### 3.D Font Inconsistency (Low Priority)
Windows uses `'Segoe UI'` which is Windows-specific. Linux also uses `'Segoe UI'` despite CLAUDE.md noting `TkDefaultFont` should be used for cross-platform compatibility.

**Recommendation**: Linux version should consistently use `'TkDefaultFont'` per documented design decision.

**Action**:
- [ ] Replace `'Segoe UI'` with `'TkDefaultFont'` in Linux GUI
- [ ] Document font choice rationale

---

## 4. Unnecessary Complexity to Remove

### 4.A Linux: Globals Update via `globals().__setitem__()` (High Priority)
Line 647 in linux_sleep_gui.pyw:
```python
sleep_type_combo.bind("<<ComboboxSelected>>",
                     lambda e: globals().__setitem__('current_sleep_type', sleep_type_combo.get()))
```

This is an unusual and overly clever way to update a global variable. It bypasses normal Python idioms and is harder to read.

**Recommendation**: Use a simple named function instead:
```python
def on_sleep_type_change(event):
    global current_sleep_type
    current_sleep_type = sleep_type_combo.get()
```

**Action**:
- [ ] Replace `globals().__setitem__()` with standard global assignment
- [ ] Create named callback functions for all widget bindings

---

### 4.B Linux: Redundant `root.update()` Calls (Medium Priority)
The Linux version calls `root.update()` inside the sleep thread loops (lines 272, 284, 348). While this ensures responsiveness, calling `root.update()` from background threads is technically unsafe in Tkinter (not thread-safe).

**Recommendation**: Either:
1. Document the threading limitation with clear comments
2. Accept current behavior as pragmatic solution (it works in practice)
3. Consider safer alternative using `root.after()` for future improvement

**Action**:
- [ ] Add comment explaining thread safety pragmatism
- [ ] Document known limitations

---

### 4.C Linux: Duplicated Process Termination Logic (Medium Priority)
Process termination for `prevent_process` appears in three places:
- `on_mode_change()` (lines 89-96)
- `cancel_operation()` (lines 227-241)
- `prevent_mode_thread()` (lines 356-361)

Each has slightly different error handling and timeout values.

**Recommendation**: Extract to a single `terminate_prevent_process()` helper with consistent error handling.

**Action**:
- [ ] Create `terminate_prevent_process(process)` helper
- [ ] Use consistent 2-second timeout everywhere
- [ ] Replace all three occurrences with function call

---

### 4.D Linux: Inhibitor Cleanup Parsing (Low Priority)
The `cleanup_gui_inhibitors()` function manually parses `systemd-inhibit --list` output, which is fragile if output format changes.

**Recommendation**: This is acceptable given the use case, but add documentation noting the format dependency.

**Action**:
- [ ] Add comment about format dependency
- [ ] Document expected `systemd-inhibit --list` output format

---

## 5. Refactoring Candidates

### 5.A Create Shared `gui_helpers.py` Module (High Priority)
Extract these components:
- `ToolTip` class
- `format_countdown(seconds)` function
- `calculate_progress(elapsed, total)` function
- `validate_positive_integer(value, field_name)` function
- `reset_ui_to_idle()` function
- Constants like progress bar style names
- `GUIState` dataclass (if implemented)

**Structure**:
```
gui_helpers.py
├── ToolTip class
├── GUIState dataclass (optional)
├── Utility functions
│   ├── format_countdown()
│   ├── calculate_progress()
│   ├── validate_positive_integer()
│   ├── reset_ui_to_idle()
│   └── build_confirm_message()
└── Constants
    ├── TIMEOUT
    └── Style definitions
```

**Action**:
- [ ] Create `gui_helpers.py`
- [ ] Move all shared components
- [ ] Update imports in both GUI files

---

### 5.B Standardize Settings Window Architecture (Medium Priority)
Both settings windows could be built using a common pattern:
- Shared cycling options section builder
- Shared about section builder
- Platform-specific sections added as needed

**Action**:
- [ ] Create `build_cycling_frame(parent, cycling_var, wait_spinbox_var)`
- [ ] Create `build_about_frame(parent, version_text)`
- [ ] Reduce `open_settings()` complexity in both files

---

### 5.C Error Handling Consolidation (Low Priority)
The Linux version has more robust error handling. Consider adding similar granularity to Windows or documenting the difference.

**Action**:
- [ ] Document error handling strategy differences
- [ ] Add consistent try/except patterns where appropriate

---

## 6. Implementation Roadmap

### Phase 1: Quick Wins (Low Risk, Low Effort)
Priority: **Do First**

1. **Extract ToolTip class** → `gui_helpers.py`
   - Time: ~5 minutes
   - Risk: Very low (simple class, no dependencies)
   - Impact: Eliminates duplication

2. **Fix `globals().__setitem__()` anti-pattern**
   - Time: ~10 minutes
   - Risk: Very low (simple function replacement)
   - Impact: Improves readability significantly

3. **Create utility functions**
   - `format_countdown()`
   - `calculate_progress()`
   - `validate_positive_integer()`
   - Time: ~15 minutes
   - Risk: Low (simple, well-defined functions)
   - Impact: Eliminates duplicated logic

4. **Consolidate process termination** (Linux only)
   - Time: ~10 minutes
   - Risk: Low (consolidates existing code)
   - Impact: Reduces code duplication

### Phase 2: Medium Effort (Medium Risk, Medium Effort)
Priority: **Do If Preparing for Unified GUI**

5. **Extract countdown logic** → shared `countdown_timer()` function
   - Time: ~30-45 minutes
   - Risk: Medium (tests needed on both platforms)
   - Impact: DRY principle, single source of truth for countdown

6. **Standardize naming conventions**
   - Time: ~15 minutes
   - Risk: Low (search and replace)
   - Impact: Better code consistency

7. **Reorganize module structure**
   - Time: ~20 minutes
   - Risk: Very low (organization only, no logic change)
   - Impact: Improved readability

### Phase 3: Advanced (Higher Risk, Higher Effort)
Priority: **Do If Planning Unified GUI**

8. **Implement GUIState dataclass** (optional)
   - Time: ~30-45 minutes
   - Risk: Medium (refactoring required)
   - Impact: Better state management

9. **Extract settings window components**
   - Time: ~30 minutes
   - Risk: Medium (UI layout must remain consistent)
   - Impact: Reduces settings code duplication

---

## 7. Summary: Prioritized Improvements

| Priority | Improvement | Effort | Impact | Prerequisite |
|----------|-------------|--------|--------|--------------|
| High | Extract `ToolTip` to shared module | Low | Medium | None |
| High | Fix `globals().__setitem__()` anti-pattern | Low | High (clarity) | None |
| High | Create utility functions | Low | High | None |
| Medium | Extract countdown timer logic | Medium | High | Phase 1 complete |
| Medium | Consolidate UI reset pattern | Low | Medium | Phase 1 complete |
| Medium | Standardize naming conventions | Low | Medium | None |
| Medium | Extract process termination logic | Low | Medium | None |
| Medium | Reorganize module-level code | Medium | Medium | None |
| Low | Fix Linux font inconsistency | Low | Low | None |
| Low | Add thread-safety documentation | Low | Low | None |

---

## 8. Notes

### For Unified GUI Strategy
If you decide to create a unified `sleep_gui.pyw`:
- **Complete Phase 1 first** - Core logic will be more testable
- **Complete Phase 2 countdown extraction** - Essential for unified GUI
- **Then merge both files** - Much easier with shared components
- Use `if sys.platform == "win32":` for conditional UI sections

### For Separate GUI Strategy
If keeping separate GUIs:
- **Complete Phase 1-2** - Makes each file cleaner
- Both benefit equally from improvements
- **No need for Phase 3** - Keep independent

### Best Practice: Shared Utilities First
Either way, extracting `gui_helpers.py` and core utilities provides immediate value without committing to larger refactoring.

---

## 8. Testing Checklist

After implementing improvements, verify:

**Windows GUI**:
- [ ] Countdown timer works (0 minutes, 1 minute, 5 minutes)
- [ ] Cancel button responsive during countdown
- [ ] Progress bar updates smoothly
- [ ] Settings save/load correctly
- [ ] Cycling enable/disable works
- [ ] Error messages display properly

**Linux GUI**:
- [ ] Mode switching (Sleep ↔ Prevent) works
- [ ] Cancel button responsive during countdown
- [ ] Prevent sleep mode works
- [ ] Mode switch cleans up prevent process
- [ ] Settings save/load correctly
- [ ] All tooltips display correctly

**Both Platforms**:
- [ ] Shared functions work on both
- [ ] No import errors
- [ ] Logging works correctly
- [ ] Application exits cleanly

---

## 9. Future Considerations

- Consider adding unit tests for utility functions
- Document platform differences clearly
- Consider logging library usage patterns
- Plan for potential macOS GUI implementation
- Document thread safety assumptions
