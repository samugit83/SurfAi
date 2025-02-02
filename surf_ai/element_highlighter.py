class ElementHighlighter:
    def __init__(self, logger):
        self.logger = logger

    def apply_highlight(self, page):
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
            
            # Wait until the DOM stops changing (i.e. no mutations for 2 seconds).
            page.evaluate("""
                async () => {
                    await new Promise(resolve => {
                        let timeout = null;
                        const observer = new MutationObserver(() => {
                            if (timeout) clearTimeout(timeout);
                            // Reset the timer on every mutation.
                            timeout = setTimeout(() => {
                                observer.disconnect();
                                resolve();
                            }, 2000);  // 2-second quiet period
                        });
                        observer.observe(document.body, {
                            childList: true,
                            subtree: true,
                            attributes: true
                        });
                        // In case there are no mutations at all, resolve after 2 seconds.
                        timeout = setTimeout(() => {
                            observer.disconnect();
                            resolve();
                        }, 2000);
                    });
                }
            """)
            page.evaluate(self._highlight_script())
        except Exception as e:
            self.logger.debug(f"Highlight failed: {str(e)}")

    def remove_highlight(self, page):
        try:
            page.evaluate(self._remove_highlight_script())
        except Exception as e:
            self.logger.debug(f"Remove highlight failed: {str(e)}") 



    def _highlight_script(self):
        # This script finds interactive elements and overlays them with a border and label.
        # For void elements (which cannot have children), a wrapper is inserted.
        return """
            (function() {
                let counter = 1;
                const getRandomColor = () => {
                    const hue = Math.floor(Math.random() * 360);
                    const saturation = 70 + Math.floor(Math.random() * 20);
                    const lightness = 30 + Math.floor(Math.random() * 10);
                    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                };

                const interactiveSelectors = [ 
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
                ];

                // List of HTML void elements (self-closing)
                const voidElements = [
                    'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                    'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'
                ];

                // Select only visible, interactive elements that haven't been highlighted yet.
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' &&
                        style.visibility === 'visible' &&
                        el.offsetParent !== null &&
                        interactiveSelectors.some(selector => el.matches(selector)) &&
                        !el.dataset.highlightNumber;
                });

                elements.forEach(el => {
                    let container = el;
                    // If the element is a void element, wrap it in a container.
                    if (voidElements.includes(el.tagName.toLowerCase())) {
                        const wrapper = document.createElement('span');
                        // Use inline-block to mimic the original element's display, if needed.
                        wrapper.style.display = 'inline-block';
                        wrapper.style.position = 'relative';
                        // Insert the wrapper before the element and then move the element into it.
                        el.parentNode.insertBefore(wrapper, el);
                        wrapper.appendChild(el);
                        container = wrapper;
                    }

                    const number = counter++;
                    const color = getRandomColor();
                    // Mark the original element (or its container) as highlighted.
                    el.dataset.highlightNumber = number;

                    // Ensure the container has positioning so that an absolutely positioned child will be relative.
                    const containerStyle = window.getComputedStyle(container);
                    if (containerStyle.position === 'static') {
                        container.style.position = 'relative';
                    }

                    // Create an overlay that fills the container.
                    const overlay = document.createElement('div');
                    overlay.className = 'surf-ai-highlight-overlay';
                    overlay.dataset.highlightNumber = number;
                    overlay.style.position = 'absolute';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.width = '100%';
                    overlay.style.height = '100%';
                    overlay.style.border = '2px solid ' + color;
                    overlay.style.boxSizing = 'border-box';
                    overlay.style.pointerEvents = 'none'; // so the overlay doesn't block interactions

                    // Set the overlay's z-index to be 5 more than the container's.
                    let currentZ = parseInt(containerStyle.zIndex, 10);
                    if (isNaN(currentZ)) {
                        currentZ = 0;
                    }
                    overlay.style.zIndex = currentZ + 5;
 
                    // Create and style the label.
                    const label = document.createElement('span');
                    label.className = 'surf-ai-highlight-label';
                    label.textContent = number;
                    label.style.position = 'absolute';
                    label.style.top = '0px';
                    label.style.left = '0px';
                    label.style.backgroundColor = color;
                    label.style.fontFamily = 'Arial';
                    label.style.color = 'white';
                    label.style.height = '15px';
                    label.style.display = 'flex';
                    label.style.alignItems = 'center';
                    label.style.justifyContent = 'center';
                    label.style.fontSize = '13px';
                    label.style.fontWeight = 'bold';
                    label.style.borderRadius = '2px';


                    overlay.appendChild(label);
                    // Append the overlay as a child of the container (either the original element or its wrapper).
                    container.appendChild(overlay);
                });
            })();
        """
    
    def _remove_highlight_script(self):
        return """
            (function() {
                // Remove all highlight overlays.
                document.querySelectorAll('.surf-ai-highlight-overlay').forEach(overlay => {
                    overlay.parentNode.removeChild(overlay);
                });
                // Remove the data-highlight-number attribute from elements. 
                document.querySelectorAll('[data-highlight-number]').forEach(el => {
                    delete el.dataset.highlightNumber;
                });
            })();
        """  