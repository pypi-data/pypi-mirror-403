# EzQt Widgets – Style Guide

## Summary

### **Inputs**
- [AutoCompleteInput](#autocompleteinput)
- [SearchInput](#searchinput)
- [TabReplaceTextEdit](#tabreplacetextedit)

### **Labels**
- [ClickableTagLabel](#clickabletaglabel)
- [HoverLabel](#hoverlabel)
- [IndicatorLabel](#indicatorlabel)

### **Buttons**
- [DateButton](#datebutton)
- [LoaderButton](#loaderbutton)
- [IconButton](#iconbutton)

### **Misc**
- [CircularTimer](#circulartimer)
- [DraggableList](#draggablelist)
- [OptionSelector](#optionselector)
- [ToggleIcon](#toggleicon)
- [ToggleSwitch](#toggleswitch)

---

This document defines the style conventions (QSS) for custom widgets in the EzQt Widgets project.

## General Principles
- Use consistent colors, borders, and rounded corners for all widgets.
- Prefer specific QSS selectors for each custom component.
- Centralize colors and spacing to facilitate maintenance.

---

### AutoCompleteInput
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#autocompleteinput)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
AutoCompleteInput {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
    selection-color: #ffffff;
    selection-background-color: #0078d4;
}
AutoCompleteInput:hover {
    background-color: #2d2d2d;
    border: 1px solid #666666;
    border-radius: 4px 4px 4px 4px;
}
AutoCompleteInput:focus {
    background-color: #2d2d2d;
    border: 1px solid #0078d4;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### SearchInput
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#searchinput)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
SearchInput {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
    selection-color: #ffffff;
    selection-background-color: #0078d4;
}
SearchInput:hover {
    background-color: #2d2d2d;
    border: 1px solid #666666;
    border-radius: 4px 4px 4px 4px;
}
SearchInput:focus {
    background-color: #2d2d2d;
    border: 1px solid #0078d4;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### TabReplaceTextEdit
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#tabreplacetextedit)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
TabReplaceTextEdit {
    background-color: #2d2d2d;
    border-radius: 5px;
    padding: 10px;
    selection-color: #ffffff;
    selection-background-color: #0078d4;
}
TabReplaceTextEdit QScrollBar:vertical {
    width: 8px;
}
TabReplaceTextEdit QScrollBar:horizontal {
    height: 8px;
}
TabReplaceTextEdit:hover {
    border: 2px solid #666666;
}
TabReplaceTextEdit:focus {
    border: 2px solid #0078d4;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Scrollbars are customized for better integration.
- Type properties are automatically defined in the code.

---

### ClickableTagLabel
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#clickabletaglabel)

<details>
<summary>View QSS</summary>

```css
/* Main widget - unselected state */
ClickableTagLabel[status="unselected"] {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
}

/* Main widget - selected state */
ClickableTagLabel[status="selected"] {
    background-color: #2d2d2d;
    border: 1px solid #0078d4;
    border-radius: 4px 4px 4px 4px;
}

/* Internal label */
ClickableTagLabel QLabel {
    background-color: transparent;
    border: none;
    border-radius: 4px 4px 4px 4px;
    color: #ffffff;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.
- Use the `status_color` property to customize the selected text color.

---

### HoverLabel
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#hoverlabel)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
HoverLabel {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### IndicatorLabel
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#indicatorlabel)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
IndicatorLabel {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### DateButton
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#datebutton)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
DateButton {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
    selection-color: #ffffff;
    selection-background-color: #0078d4;
}
DateButton:hover {
    background-color: #2d2d2d;
    border: 1px solid #666666;
    border-radius: 4px 4px 4px 4px;
}
DateButton:focus {
    background-color: #2d2d2d;
    border: 1px solid #0078d4;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### LoaderButton
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#loaderbutton)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
LoaderButton {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
    selection-color: #ffffff;
    selection-background-color: #0078d4;
}
LoaderButton:hover {
    background-color: #2d2d2d;
    border: 1px solid #666666;
    border-radius: 4px 4px 4px 4px;
}
LoaderButton:focus {
    background-color: #2d2d2d;
    border: 1px solid #0078d4;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### IconButton
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#iconbutton)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
IconButton {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
    selection-color: #ffffff;
    selection-background-color: #0078d4;
}
IconButton:hover {
    background-color: #2d2d2d;
    border: 1px solid #666666;
    border-radius: 4px 4px 4px 4px;
}
IconButton:focus {
    background-color: #2d2d2d;
    border: 1px solid #0078d4;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.

---

### CircularTimer
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#circulartimer)

**Note:** This widget does not use QSS for customization. Colors and appearance are controlled via Python properties:

- `ring_color`: Color of the progress arc (QColor, str)
- `node_color`: Color of the center (QColor, str)
- `ring_width_mode`: Arc thickness ("small", "medium", "large")
- `pen_width`: Custom thickness (prioritizes ring_width_mode)

**Example usage:**
```python
timer = CircularTimer(
    ring_color="#0078d4",
    node_color="#ffffff", 
    ring_width_mode="medium",
    loop=True
)
```

---

### OptionSelector
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#optionselector)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
OptionSelector {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 4px 4px 4px 4px;
}

/* Animated selector */
OptionSelector [type="OptionSelector_Selector"] {
    background-color: #0078d4;
    border: none;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.
- The animated selector automatically adapts to the selected option.

---

### ToggleIcon
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#toggleicon)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
ToggleIcon {
    background-color: #2d2d2d;
    border: none;
    border-radius: 4px 4px 4px 4px;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.
- The widget uses either custom icons or draws triangles in paintEvent.

---

### ToggleSwitch
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#toggleswitch)

<details>
<summary>View QSS</summary>

```css
/* Main widget */
ToggleSwitch {
	background-color: $_main_border;
	border: 2px solid $_accent_color1;
	border-radius: 12px;
}

ToggleSwitch:hover {
	border: 2px solid $_accent_color4;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.
- The widget uses CSS variables for colors ($_main_border, $_accent_color1, $_accent_color4).

---

### DraggableList
[⬆️ Back to top](#summary) | [📖 Complete documentation](WIDGETS_DOCUMENTATION.md#draggablelist)

<details>
<summary>View QSS</summary>

```css
/* /////////////////////////////////////////////////////////////////////////////////////////////////
DraggableList */
DraggableList {
	background-color: $_main_border;
	border: 2px solid $_accent_color1;
	border-radius: 6px;
	padding: 8px;
	color: rgb(255, 255, 255);
}

DraggableList QScrollArea {
	background-color: $_main_surface;
	border: 2px solid $_accent_color1;
	border-radius: 6px;
	padding: 4px 0px 4px 4px;
}

DraggableList QScrollArea QWidget {
	background-color: transparent;
	border: none;
}

[type="DraggableItem"] {
	background-color: $_main_border;
	border: 1px solid $_accent_color1;
	border-radius: 6px 6px 6px 6px;
}

[type="DraggableItem"]:hover {
	background-color: $_accent_color1;
	border: 2px solid $_accent_color4;
}

[type="DraggableItem"][dragging="true"] {
	background-color: $_accent_color4;
	color: $_select_text_color;
}

[type="DraggableItem"] QLabel {
	background-color: transparent;
	border: none;
	color: $_base_text_color;
}
```
</details>

- Adapt colors according to your application's graphic charter.
- Type properties are automatically defined in the code.
- The widget uses CSS variables for colors ($_main_border, $_accent_color1, $_accent_color4, $_main_surface, $_select_text_color, $_base_text_color).
- The `dragging="true"` state is automatically applied during drag & drop.

---

## Good Practices

[⬆️ Back to top](#summary)

- Type properties are automatically defined in the code of widgets.
- Document each QSS section in this file.
- Test appearance on different OS and Qt themes.
- Use consistent colors for selection (selection-color and selection-background-color). 

