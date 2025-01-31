class ElementHighlighter:
    def __init__(self, logger):
        self.logger = logger

    def apply_highlight(self, page):
        try:
            page.wait_for_function('''() => document.readyState === 'complete' ''', timeout=5000)
            page.evaluate(self._highlight_script())
        except Exception as e:
            self.logger.debug(f"Highlight failed: {str(e)}")

    def remove_highlight(self, page):
        try:
            page.evaluate(self._remove_highlight_script())
        except Exception as e:
            self.logger.debug(f"Remove highlight failed: {str(e)}")

    def _highlight_script(self):
        return """
                let counter = 1;
                const getRandomColor = () => {
                    const hue = Math.floor(Math.random() * 360);
                    const saturation = 70 + Math.floor(Math.random() * 20); 
                    const lightness = 30 + Math.floor(Math.random() * 10);  
                    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                };

                interactiveSelectors = [
                    'input', 'textarea', 'button', 'select', 'output',
                    'a[href]', 'area[href]',
                    '[contenteditable]', 
                    '[tabindex]:not([tabindex="-1"])',
                    '[onclick]', '[ondblclick]', '[onchange]', '[onsubmit]', '[onkeydown]',
                    'audio[controls]', 'video[controls]',
                    'details', 'details > summary',
                    '[role="button"]', '[role="checkbox"]', '[role="radio"]',
                    '[role="link"]', '[role="textbox"]', '[role="searchbox"]',
                    '[role="combobox"]', '[role="listbox"]', '[role="menu"]',
                    '[role="menuitem"]', '[role="slider"]', '[role="switch"]',
                    '[role="tab"]', '[role="treeitem"]', '[role="gridcell"]',
                    '[role="option"]', '[role="spinbutton"]', '[role="scrollbar"]',
                    'iframe', 'object', 'embed'
                ]
                const voidElements = ['input', 'img', 'br', 'hr', 'area', 'base', 'col', 'select', 'textarea',
                                    'embed', 'link', 'meta', 'param', 'source', 'track', 'wbr'];
                
                // Clear previous body labels
                if (window.surfAiLabels) {
                    window.surfAiLabels.forEach(label => label.remove()); 
                    window.surfAiLabels = [];
                }
                
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                        style.visibility === 'visible' &&
                        el.offsetParent !== null &&
                        interactiveSelectors.some(selector => el.matches(selector)) &&
                        !el.dataset.highlightNumber;
                });

                elements.forEach(el => {
                    el.style.overflow = 'visible';
                    const number = counter++;
                    const tagName = el.tagName.toLowerCase(); 

                    el.dataset.originalBorder = el.style.border || '';
                    el.dataset.originalBoxSizing = el.style.boxSizing || '';
                    el.dataset.originalPosition = el.style.position || '';
                    
                    el.dataset.highlightNumber = number; 
                    const color = getRandomColor();
                    el.style.border = `2px solid ${color}`; 
                    el.style.boxSizing = 'border-box';
                    el.style.position = 'relative';

                    const label = document.createElement('span'); 
                    label.className = 'surf-ai-highlight-label';
                    label.textContent = number;
                    label.style.backgroundColor = color;
                    label.style.fontFamily = 'Arial';
                    label.style.mixBlendMode = 'normal';
                    label.style.pointerEvents = 'none';
                    label.style.color = 'white';
                    label.style.padding = '0 4px';
                    label.style.height = '21px';
                    label.style.display = 'flex'; 
                    label.style.alignItems = 'center';
                    label.style.justifyContent = 'center';
                    label.style.fontSize = '17px';
                    label.style.fontWeight = 'bold'; 
                    label.style.borderRadius = '2px';
                    label.style.zIndex = '99999';

                    if (voidElements.includes(tagName)) {
                        const rect = el.getBoundingClientRect();
                        const scrollX = window.pageXOffset;
                        const scrollY = window.pageYOffset;
                        
                        // Find the first positioned ancestor
                        let parent = el.parentElement;
                        let positionedParent = null;
                        while (parent) {
                            const style = getComputedStyle(parent);
                            if (style.position !== 'static') {
                                positionedParent = parent;  
                                break; 
                            }
                            parent = parent.parentElement;
                        }

                        if (positionedParent) { 
                            const parentRect = positionedParent.getBoundingClientRect();
                            label.style.position = 'absolute';
                            label.style.top = `${rect.top - parentRect.top + scrollY}px`;
                            label.style.left = `${rect.left - parentRect.left + scrollX}px`;
                            positionedParent.appendChild(label);
                        } else {
                            label.style.position = 'absolute';
                            label.style.top = `${rect.top + scrollY}px`;
                            label.style.left = `${rect.left + scrollX}px`;
                            document.body.appendChild(label);
                        }

                        const labelRect = label.getBoundingClientRect();
                        if (labelRect.right > window.innerWidth) {
                            label.style.left = `${rect.left + scrollX}px`;
                        }
                        if (labelRect.bottom > window.innerHeight) {
                            label.style.top = `${rect.top + scrollY - labelRect.height}px`;
                        }

                        if (labelRect.left < 0) {
                            label.style.left = `${scrollX}px`;
                        }

                        if (!window.surfAiLabels) window.surfAiLabels = [];
                        window.surfAiLabels.push(label);

                    } else {
                        // Position relative to parent element 
                        label.style.position = 'absolute'; 
                        label.style.top = '0px';
                        label.style.left = '0px';
                        el.appendChild(label);
                    }
                });
            """
    
    def _remove_highlight_script(self):
        return """

                if (window.surfAiLabels) {
                    window.surfAiLabels.forEach(label => label.remove());
                    window.surfAiLabels = [];
                }
                
                const elements = Array.from(document.querySelectorAll('*[data-highlight-number]'));
                elements.forEach(el => {
                    const labels = el.getElementsByClassName('surf-ai-highlight-label');
                    while(labels.length > 0) {
                        labels[0].remove();
                    } 
                    
                    el.style.border = el.dataset.originalBorder || '';
                    el.style.boxSizing = el.dataset.originalBoxSizing || '';
                    el.style.position = el.dataset.originalPosition || '';  

                    delete el.dataset.highlightNumber;
                    delete el.dataset.originalBorder;
                    delete el.dataset.originalBoxSizing;
                    delete el.dataset.originalPosition;
                });
            """