/**
 * A2UI Dynamic Widgets Renderer
 * Handles rendering and interaction with AI-generated widgets
 */

class WidgetRenderer {
    constructor() {
        this.widgets = {};
        this.widgetData = {};
    }

    /**
     * Render widgets from A2UI response
     */
    renderWidgets(parts) {
        console.log('[WidgetRenderer] renderWidgets called with', parts.length, 'parts');
        const widgetsContent = document.getElementById('widgets-content');
        widgetsContent.innerHTML = '';
        this.widgets = {};
        this.widgetData = {};

        // Extract widgets from A2UI Surface format or legacy format
        const widgets = this.extractWidgets(parts);
        
        console.log('[WidgetRenderer] Extracted widgets:', widgets.length);
        
        if (widgets.length === 0) {
            console.log('[WidgetRenderer] No widgets found, returning false');
            return false;
        }

        widgets.forEach(widget => {
            console.log('[WidgetRenderer] Creating widget:', widget.type, widget.id);
            const widgetElement = this.createWidgetDynamic(widget);
            if (widgetElement) {
                widgetsContent.appendChild(widgetElement);
                this.widgets[widget.id] = widget;
                // Initialize widget data with default values
                this.widgetData[widget.id] = this.getDefaultValues(widget);
                console.log('[WidgetRenderer] Widget created successfully');
            } else {
                console.warn('[WidgetRenderer] Failed to create widget element');
            }
        });

        console.log('[WidgetRenderer] Total widgets rendered:', Object.keys(this.widgets).length);
        return true;
    }

    /**
     * Extract widgets from various A2UI formats
     */
    extractWidgets(parts) {
        const widgets = [];
        let dataModel = {};
        
        // First pass: extract data model
        for (const part of parts) {
            if (part.kind === 'data' && part.data && part.data.dataModelUpdate) {
                console.log('[WidgetRenderer] Found dataModelUpdate');
                const contents = part.data.dataModelUpdate.contents || [];
                for (const content of contents) {
                    dataModel[content.key] = content.valueString || content.valueInt || content.valueNumber || content.valueBoolean;
                }
                console.log('[WidgetRenderer] Data model:', dataModel);
            }
        }
        
        // Store data model for getPathValue
        this.currentDataModel = dataModel;
        
        // Second pass: extract widgets
        for (const part of parts) {
            // Format 1: Legacy simple a2ui parts
            if ((part.kind === 'a2ui' && part.a2ui) || part.a2ui) {
                widgets.push(part.a2ui);
                console.log('[WidgetRenderer] Found legacy widget:', part.a2ui.type);
            }
            // Format 2: A2UI Surface format with surfaceUpdate
            else if (part.kind === 'data' && part.data && part.data.surfaceUpdate) {
                console.log('[WidgetRenderer] Found surfaceUpdate with components');
                const components = part.data.surfaceUpdate.components || [];
                
                for (const comp of components) {
                    const widget = this.convertSurfaceComponentToWidget(comp);
                    if (widget) {
                        widgets.push(widget);
                        console.log('[WidgetRenderer] Converted surface component to widget:', widget.type);
                    }
                }
            }
        }
        
        return widgets;
    }

    /**
     * Convert A2UI Surface component to simple widget format
     */
    convertSurfaceComponentToWidget(component) {
        const id = component.id;
        const comp = component.component;
        
        if (!comp || !id) return null;
        
        // Generate a better label from the component ID (e.g., "size-slider" -> "Size")
        const generateLabel = (id, defaultLabel) => {
            const label = comp[Object.keys(comp)[0]]?.label?.literalString;
            if (label) return label;
            
            // Convert ID to readable label: "size-slider" -> "Size", "color-input" -> "Color"
            const cleaned = id.replace(/-slider|-input|-field|-widget|-control/gi, '');
            return cleaned.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') || defaultLabel;
        };
        
        // Check component type
        if (comp.Slider) {
            const pathValue = comp.Slider.value?.path ? this.getPathValue(comp.Slider.value.path) : null;
            const defaultValue = pathValue !== null ? pathValue : (comp.Slider.minValue || 0);
            
            return {
                id: id,
                type: 'slider',
                label: generateLabel(id, 'Slider'),
                properties: {
                    min: comp.Slider.minValue || 0,
                    max: comp.Slider.maxValue || 100,
                    default: defaultValue,
                    step: comp.Slider.stepSize || 1
                }
            };
        } else if (comp.TextField) {
            const pathValue = comp.TextField.value?.path ? this.getPathValue(comp.TextField.value.path) : null;
            
            return {
                id: id,
                type: 'text-input',
                label: generateLabel(id, 'Text'),
                properties: {
                    default: pathValue || '',
                    hint: comp.TextField.hintText?.literalString || ''
                }
            };
        } else if (comp.Select) {
            const pathValue = comp.Select.value?.path ? this.getPathValue(comp.Select.value.path) : null;
            
            return {
                id: id,
                type: 'dropdown',
                label: generateLabel(id, 'Select'),
                properties: {
                    options: comp.Select.options || [],
                    default: pathValue || (comp.Select.options && comp.Select.options[0])
                }
            };
        } else if (comp.Switch) {
            const pathValue = comp.Switch.value?.path ? this.getPathValue(comp.Switch.value.path) : null;
            
            return {
                id: id,
                type: 'toggle',
                label: generateLabel(id, 'Toggle'),
                properties: {
                    default: pathValue !== null ? pathValue : false
                }
            };
        }
        // Skip Image, Text, Column components - they're not interactive widgets
        else if (comp.Image || comp.Text || comp.Column || comp.Row) {
            console.log('[WidgetRenderer] Skipping non-interactive component:', Object.keys(comp)[0]);
            return null;
        }
        
        console.warn('[WidgetRenderer] Unknown component type:', Object.keys(comp));
        return null;
    }

    /**
     * Get value from data model path
     */
    getPathValue(path) {
        // Extract key from path (e.g., "/size" -> "size")
        const key = path.replace(/^\//, '');
        const value = this.currentDataModel ? this.currentDataModel[key] : null;
        console.log('[WidgetRenderer] getPathValue:', path, '->', value);
        return value;
    }

    /**
     * Get default values for a widget
     */
    getDefaultValues(widget) {
        const props = widget.properties || {};
        const defaults = {};
        
        switch(widget.type) {
            case 'slider':
                defaults.value = props.default || props.min || 0;
                break;
            case 'color-picker':
                defaults.color = props.default || '#000000';
                break;
            case 'sketch-canvas':
                defaults.sketch = null;
                break;
            case 'dropdown':
                defaults.value = props.default || (props.options && props.options[0]) || '';
                break;
            case 'text-input':
                defaults.value = props.default || '';
                break;
            case 'toggle':
                defaults.value = props.default || false;
                break;
            case 'range-dual':
                defaults.min = props.defaultMin || props.min || 0;
                defaults.max = props.defaultMax || props.max || 100;
                break;
        }
        
        return defaults;
    }

    /**
     * Create a widget element dynamically based on type
     */
    createWidgetDynamic(widget) {
        // Map widget types to creation functions
        const creators = {
            'slider': this.createSlider.bind(this),
            'color-picker': this.createColorPicker.bind(this),
            'sketch-canvas': this.createSketchCanvas.bind(this),
            'dropdown': this.createDropdown.bind(this),
            'text-input': this.createTextInput.bind(this),
            'toggle': this.createToggle.bind(this),
            'range-dual': this.createDualRange.bind(this),
            // Backward compatibility
            'color-tone-control': this.createColorToneWidget.bind(this),
            'sketch-board': this.createSketchBoardWidget.bind(this)
        };
        
        const creator = creators[widget.type];
        if (creator) {
            return creator(widget);
        } else {
            console.warn('Unknown widget type:', widget.type);
            return this.createGenericWidget(widget);
        }
    }

    /**
     * Create a basic slider widget
     */
    createSlider(widget) {
        const container = document.createElement('div');
        container.className = 'widget slider-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const min = props.min || 0;
        const max = props.max || 100;
        const defaultVal = props.default !== undefined ? props.default : min;
        const step = props.step || 1;

        container.innerHTML = `
            <div class="widget-title">${widget.label || 'Slider'}</div>
            <div class="control-group">
                <div class="control-label">
                    <span class="control-value" id="${widget.id}-value">${defaultVal}</span>
                </div>
                <input 
                    type="range" 
                    id="${widget.id}-input" 
                    min="${min}" 
                    max="${max}" 
                    step="${step}"
                    value="${defaultVal}"
                    data-widget-id="${widget.id}"
                >
            </div>
        `;

        // Add event listener
        const input = container.querySelector('input');
        const valueDisplay = container.querySelector(`#${widget.id}-value`);
        input.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            valueDisplay.textContent = value;
            this.widgetData[widget.id] = { value };
        });

        return container;
    }

    /**
     * Create a color picker widget
     */
    createColorPicker(widget) {
        const container = document.createElement('div');
        container.className = 'widget color-picker-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const defaultColor = props.default || '#000000';

        container.innerHTML = `
            <div class="widget-title">${widget.label || 'Color Picker'}</div>
            <div class="control-group">
                <input 
                    type="color" 
                    id="${widget.id}-input" 
                    value="${defaultColor}"
                    data-widget-id="${widget.id}"
                    style="width: 100%; height: 50px; cursor: pointer; border: none; border-radius: 4px;"
                >
                <div class="control-label" style="margin-top: 8px;">
                    <span class="control-value" id="${widget.id}-value">${defaultColor}</span>
                </div>
            </div>
        `;

        // Add event listener
        const input = container.querySelector('input');
        const valueDisplay = container.querySelector(`#${widget.id}-value`);
        input.addEventListener('input', (e) => {
            const color = e.target.value;
            valueDisplay.textContent = color;
            this.widgetData[widget.id] = { color };
        });

        return container;
    }

    /**
     * Create a sketch canvas widget
     */
    createSketchCanvas(widget) {
        const container = document.createElement('div');
        container.className = 'widget sketch-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const width = props.width || 512;
        const height = props.height || 512;

        container.innerHTML = `
            <div class="widget-title">${widget.label || 'Sketch Canvas'}</div>
            <div class="sketch-controls">
                <button class="sketch-btn" id="${widget.id}-clear">Clear</button>
                <input type="color" id="${widget.id}-color" value="#000000" style="width: 50px;">
                <input type="range" id="${widget.id}-size" min="1" max="20" value="3" style="width: 100px;">
                <span id="${widget.id}-size-label">3px</span>
            </div>
            <canvas 
                id="${widget.id}-canvas" 
                width="${width}" 
                height="${height}"
                data-widget-id="${widget.id}"
                style="border: 1px solid #ccc; cursor: crosshair; background: white; display: block; margin-top: 8px;"
            ></canvas>
        `;

        // Setup canvas drawing
        const canvas = container.querySelector('canvas');
        const ctx = canvas.getContext('2d');
        const clearBtn = container.querySelector(`#${widget.id}-clear`);
        const colorInput = container.querySelector(`#${widget.id}-color`);
        const sizeInput = container.querySelector(`#${widget.id}-size`);
        const sizeLabel = container.querySelector(`#${widget.id}-size-label`);

        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;

        // Clear canvas with white background
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, width, height);

        canvas.addEventListener('mousedown', (e) => {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            lastX = e.clientX - rect.left;
            lastY = e.clientY - rect.top;
        });

        canvas.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            ctx.strokeStyle = colorInput.value;
            ctx.lineWidth = parseInt(sizeInput.value);
            ctx.lineCap = 'round';
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(x, y);
            ctx.stroke();

            lastX = x;
            lastY = y;
        });

        canvas.addEventListener('mouseup', () => {
            isDrawing = false;
            // Save canvas data
            this.widgetData[widget.id] = { sketch: canvas.toDataURL() };
        });

        canvas.addEventListener('mouseleave', () => {
            isDrawing = false;
        });

        clearBtn.addEventListener('click', () => {
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, width, height);
            this.widgetData[widget.id] = { sketch: null };
        });

        sizeInput.addEventListener('input', (e) => {
            sizeLabel.textContent = `${e.target.value}px`;
        });

        return container;
    }

    /**
     * Create a dropdown widget
     */
    createDropdown(widget) {
        const container = document.createElement('div');
        container.className = 'widget dropdown-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const options = props.options || [];
        const defaultValue = props.default || (options.length > 0 ? options[0] : '');

        const optionsHTML = options.map(opt => 
            `<option value="${opt}" ${opt === defaultValue ? 'selected' : ''}>${opt}</option>`
        ).join('');

        container.innerHTML = `
            <div class="widget-title">${widget.label || 'Dropdown'}</div>
            <div class="control-group">
                <select 
                    id="${widget.id}-input" 
                    data-widget-id="${widget.id}"
                    style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;"
                >
                    ${optionsHTML}
                </select>
            </div>
        `;

        // Add event listener
        const select = container.querySelector('select');
        select.addEventListener('change', (e) => {
            this.widgetData[widget.id] = { value: e.target.value };
        });

        // Initialize data
        this.widgetData[widget.id] = { value: defaultValue };

        return container;
    }

    /**
     * Create a text input widget
     */
    createTextInput(widget) {
        const container = document.createElement('div');
        container.className = 'widget text-input-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const defaultValue = props.default || '';
        const placeholder = props.placeholder || '';
        const multiline = props.multiline || false;

        if (multiline) {
            container.innerHTML = `
                <div class="widget-title">${widget.label || 'Text Input'}</div>
                <div class="control-group">
                    <textarea 
                        id="${widget.id}-input" 
                        data-widget-id="${widget.id}"
                        placeholder="${placeholder}"
                        style="width: 100%; min-height: 80px; padding: 8px; border-radius: 4px; border: 1px solid #ccc; font-family: inherit;"
                    >${defaultValue}</textarea>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="widget-title">${widget.label || 'Text Input'}</div>
                <div class="control-group">
                    <input 
                        type="text" 
                        id="${widget.id}-input" 
                        data-widget-id="${widget.id}"
                        placeholder="${placeholder}"
                        value="${defaultValue}"
                        style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;"
                    >
                </div>
            `;
        }

        // Add event listener
        const input = container.querySelector(multiline ? 'textarea' : 'input');
        input.addEventListener('input', (e) => {
            this.widgetData[widget.id] = { value: e.target.value };
        });

        // Initialize data
        this.widgetData[widget.id] = { value: defaultValue };

        return container;
    }

    /**
     * Create a toggle/switch widget
     */
    createToggle(widget) {
        const container = document.createElement('div');
        container.className = 'widget toggle-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const defaultValue = props.default || false;

        container.innerHTML = `
            <div class="widget-title">${widget.label || 'Toggle'}</div>
            <div class="control-group">
                <label class="toggle-switch">
                    <input 
                        type="checkbox" 
                        id="${widget.id}-input" 
                        data-widget-id="${widget.id}"
                        ${defaultValue ? 'checked' : ''}
                    >
                    <span class="toggle-slider"></span>
                </label>
            </div>
        `;

        // Add CSS for toggle switch
        if (!document.getElementById('toggle-switch-styles')) {
            const style = document.createElement('style');
            style.id = 'toggle-switch-styles';
            style.textContent = `
                .toggle-switch {
                    position: relative;
                    display: inline-block;
                    width: 60px;
                    height: 34px;
                }
                .toggle-switch input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                .toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: .4s;
                    border-radius: 34px;
                }
                .toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 26px;
                    width: 26px;
                    left: 4px;
                    bottom: 4px;
                    background-color: white;
                    transition: .4s;
                    border-radius: 50%;
                }
                input:checked + .toggle-slider {
                    background-color: #2196F3;
                }
                input:checked + .toggle-slider:before {
                    transform: translateX(26px);
                }
            `;
            document.head.appendChild(style);
        }

        // Add event listener
        const input = container.querySelector('input');
        input.addEventListener('change', (e) => {
            this.widgetData[widget.id] = { value: e.target.checked };
        });

        // Initialize data
        this.widgetData[widget.id] = { value: defaultValue };

        return container;
    }

    /**
     * Create a dual range slider widget (min/max)
     */
    createDualRange(widget) {
        const container = document.createElement('div');
        container.className = 'widget dual-range-widget';
        container.id = widget.id;

        const props = widget.properties || {};
        const min = props.min || 0;
        const max = props.max || 100;
        const defaultMin = props.defaultMin !== undefined ? props.defaultMin : min;
        const defaultMax = props.defaultMax !== undefined ? props.defaultMax : max;

        container.innerHTML = `
            <div class="widget-title">${widget.label || 'Range'}</div>
            <div class="control-group">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>Min: <span id="${widget.id}-min-value">${defaultMin}</span></span>
                    <span>Max: <span id="${widget.id}-max-value">${defaultMax}</span></span>
                </div>
                <input 
                    type="range" 
                    id="${widget.id}-min-input" 
                    min="${min}" 
                    max="${max}" 
                    value="${defaultMin}"
                    data-widget-id="${widget.id}"
                    style="width: 100%;"
                >
                <input 
                    type="range" 
                    id="${widget.id}-max-input" 
                    min="${min}" 
                    max="${max}" 
                    value="${defaultMax}"
                    data-widget-id="${widget.id}"
                    style="width: 100%; margin-top: 4px;"
                >
            </div>
        `;

        // Add event listeners
        const minInput = container.querySelector(`#${widget.id}-min-input`);
        const maxInput = container.querySelector(`#${widget.id}-max-input`);
        const minValueDisplay = container.querySelector(`#${widget.id}-min-value`);
        const maxValueDisplay = container.querySelector(`#${widget.id}-max-value`);

        const updateValues = () => {
            let minVal = parseFloat(minInput.value);
            let maxVal = parseFloat(maxInput.value);

            // Ensure min <= max
            if (minVal > maxVal) {
                minVal = maxVal;
                minInput.value = minVal;
            }

            minValueDisplay.textContent = minVal;
            maxValueDisplay.textContent = maxVal;
            this.widgetData[widget.id] = { min: minVal, max: maxVal };
        };

        minInput.addEventListener('input', updateValues);
        maxInput.addEventListener('input', updateValues);

        // Initialize data
        this.widgetData[widget.id] = { min: defaultMin, max: defaultMax };

        return container;
    }

    /**
     * Create a generic fallback widget for unknown types
     */
    createGenericWidget(widget) {
        const container = document.createElement('div');
        container.className = 'widget generic-widget';
        container.id = widget.id;

        container.innerHTML = `
            <div class="widget-title">${widget.label || widget.type}</div>
            <div style="padding: 12px; background: #f5f5f5; border-radius: 4px;">
                <p style="margin: 0; color: #666;">Widget type '${widget.type}' not yet implemented</p>
            </div>
        `;

        return container;
    }

    /**
     * Create Color Tone Control Widget
     */
    createColorToneWidget(widget) {
        const container = document.createElement('div');
        container.className = 'widget color-tone-widget';
        container.id = widget.id;

        const props = widget.properties;

        container.innerHTML = `
            <div class="widget-title">${props.title || 'Color Tone Control'}</div>
            <div class="color-control">
                <div class="control-group">
                    <div class="control-label">
                        <span>Hue</span>
                        <span class="control-value" id="${widget.id}-hue-value">${props.hue}°</span>
                    </div>
                    <input 
                        type="range" 
                        id="${widget.id}-hue" 
                        min="0" 
                        max="360" 
                        value="${props.hue}"
                        data-widget-id="${widget.id}"
                        data-property="hue"
                    >
                </div>

                <div class="control-group">
                    <div class="control-label">
                        <span>Saturation</span>
                        <span class="control-value" id="${widget.id}-saturation-value">${props.saturation}%</span>
                    </div>
                    <input 
                        type="range" 
                        id="${widget.id}-saturation" 
                        min="0" 
                        max="100" 
                        value="${props.saturation}"
                        data-widget-id="${widget.id}"
                        data-property="saturation"
                    >
                </div>

                <div class="control-group">
                    <div class="control-label">
                        <span>Lightness</span>
                        <span class="control-value" id="${widget.id}-lightness-value">${props.lightness}%</span>
                    </div>
                    <input 
                        type="range" 
                        id="${widget.id}-lightness" 
                        min="0" 
                        max="100" 
                        value="${props.lightness}"
                        data-widget-id="${widget.id}"
                        data-property="lightness"
                    >
                </div>

                <div class="control-group">
                    <div class="control-label">
                        <span>Temperature</span>
                    </div>
                    <div class="temperature-buttons">
                        <button class="temp-btn ${props.temperature === 'warm' ? 'active' : ''}" 
                                data-widget-id="${widget.id}" 
                                data-value="warm">
                            🔥 Warm
                        </button>
                        <button class="temp-btn ${props.temperature === 'neutral' ? 'active' : ''}" 
                                data-widget-id="${widget.id}" 
                                data-value="neutral">
                            ⚪ Neutral
                        </button>
                        <button class="temp-btn ${props.temperature === 'cool' ? 'active' : ''}" 
                                data-widget-id="${widget.id}" 
                                data-value="cool">
                            ❄️ Cool
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners for sliders
        container.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const widgetId = e.target.dataset.widgetId;
                const property = e.target.dataset.property;
                const value = parseFloat(e.target.value);
                
                this.widgetData[widgetId][property] = value;
                
                // Update display
                const valueDisplay = document.getElementById(`${widgetId}-${property}-value`);
                if (valueDisplay) {
                    valueDisplay.textContent = property === 'hue' ? `${value}°` : `${value}%`;
                }
            });
        });

        // Add event listeners for temperature buttons
        container.querySelectorAll('.temp-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const widgetId = e.target.dataset.widgetId;
                const value = e.target.dataset.value;
                
                this.widgetData[widgetId].temperature = value;
                
                // Update button states
                container.querySelectorAll('.temp-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        return container;
    }

    /**
     * Create Sketch Board Widget
     */
    createSketchBoardWidget(widget) {
        const container = document.createElement('div');
        container.className = 'widget sketch-board-widget';
        container.id = widget.id;

        const props = widget.properties;

        container.innerHTML = `
            <div class="widget-title">${props.title || 'Sketch Board'}</div>
            <div class="sketch-board-container">
                <div class="canvas-container">
                    <canvas 
                        id="${widget.id}-canvas" 
                        width="${props.width || 512}" 
                        height="${props.height || 512}"
                    ></canvas>
                </div>
                <div class="canvas-tools">
                    <button class="tool-btn active" data-tool="pen">✏️ Pen</button>
                    <button class="tool-btn" data-tool="eraser">🧹 Eraser</button>
                    <button class="tool-btn" data-tool="clear">🗑️ Clear</button>
                </div>
            </div>
        `;

        // Initialize canvas
        setTimeout(() => {
            const canvas = document.getElementById(`${widget.id}-canvas`);
            if (canvas) {
                this.initializeSketchBoard(canvas, widget.id, props.initialSketch);
            }
        }, 0);

        // Tool button listeners
        container.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.target.dataset.tool;
                
                if (tool === 'clear') {
                    const canvas = document.getElementById(`${widget.id}-canvas`);
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = 'white';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    this.widgetData[widget.id].sketch = null;
                } else {
                    container.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    const canvas = document.getElementById(`${widget.id}-canvas`);
                    if (canvas.sketchTool) {
                        canvas.sketchTool = tool;
                    }
                }
            });
        });

        return container;
    }

    /**
     * Initialize sketch board with drawing capabilities
     */
    initializeSketchBoard(canvas, widgetId, initialSketch) {
        const ctx = canvas.getContext('2d');
        
        // Fill with white background
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Load initial sketch if provided
        if (initialSketch) {
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0);
            };
            img.src = `data:image/png;base64,${initialSketch}`;
        }
        
        // Drawing state
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        canvas.sketchTool = 'pen';
        
        const startDrawing = (e) => {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            lastX = e.clientX - rect.left;
            lastY = e.clientY - rect.top;
        };
        
        const draw = (e) => {
            if (!isDrawing) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(x, y);
            
            if (canvas.sketchTool === 'pen') {
                ctx.strokeStyle = 'black';
                ctx.lineWidth = 2;
            } else if (canvas.sketchTool === 'eraser') {
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 20;
            }
            
            ctx.lineCap = 'round';
            ctx.stroke();
            
            lastX = x;
            lastY = y;
        };
        
        const stopDrawing = () => {
            if (isDrawing) {
                isDrawing = false;
                // Save canvas data
                this.widgetData[widgetId].sketch = canvas.toDataURL('image/png').split(',')[1];
            }
        };
        
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseleave', stopDrawing);
        
        // Touch support
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        });
        
        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        });
        
        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            const mouseEvent = new MouseEvent('mouseup', {});
            canvas.dispatchEvent(mouseEvent);
        });
    }

    /**
     * Get current widget data for sending to backend
     * Returns array of A2UI widget parts following the protocol
     */
    getWidgetData() {
        console.log('[WidgetRenderer] getWidgetData called');
        console.log('[WidgetRenderer] Current widgets:', Object.keys(this.widgets));
        console.log('[WidgetRenderer] Current widgetData:', this.widgetData);
        
        // For backward compatibility, check for old widget types first
        const result = {};
        const widgetParts = [];
        
        for (const [widgetId, widget] of Object.entries(this.widgets)) {
            if (widget.type === 'color-tone-control') {
                result.color_tone = this.widgetData[widgetId];
            } else if (widget.type === 'sketch-board') {
                if (this.widgetData[widgetId].sketch) {
                    result.sketch = this.widgetData[widgetId].sketch;
                }
            } else {
                // For dynamic widgets, preserve the widget structure per A2UI protocol
                widgetParts.push({
                    type: widget.type,
                    id: widgetId,
                    properties: this.widgetData[widgetId]
                });
            }
        }
        
        // Return old format if any old widgets present
        if (Object.keys(result).length > 0) {
            console.log('[WidgetRenderer] Returning old format:', result);
            return result;
        }
        
        // For dynamic widgets, return array of widget parts
        if (widgetParts.length > 0) {
            console.log('[WidgetRenderer] Returning widget_parts:', widgetParts);
            return { widget_parts: widgetParts };
        }
        
        console.log('[WidgetRenderer] No widget data to return');
        return null;
    }

    /**
     * Show or hide widgets panel
     */
    togglePanel(show) {
        const panel = document.getElementById('widgets-panel');
        if (show) {
            panel.classList.remove('hidden');
        } else {
            panel.classList.add('hidden');
        }
    }
}

// Export for use in other scripts
window.WidgetRenderer = WidgetRenderer;
