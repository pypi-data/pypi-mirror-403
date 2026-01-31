console.log('🔍 [DEBUG] span-manager.js file loaded!');

/**
 * Unified Positioning Strategy for Text Span Annotation
 * This class provides a unified approach to text positioning and span creation
 * that works consistently across different browsers and text layouts.
 */
class UnifiedPositioningStrategy {
    constructor(container) {
        this.container = container;
        this.fontMetrics = null;
        this.canonicalText = null;
        this.isInitialized = false;
    }

        /**
     * Initialize the positioning strategy with stable font metrics
     */
    async initialize() {
        console.log('🔍 [UNIFIED] Initializing positioning strategy');

        // Wait for DOM elements to be ready
        await this.waitForElements();
        console.log('🔍 [UNIFIED] DOM elements ready');

        // Wait for fonts to load and layout to stabilize
        await this.waitForFontMetrics();
        console.log('🔍 [UNIFIED] Fonts loaded and layout stabilized');

        // Get canonical text for positioning calculations
        const canonicalText = this.getCanonicalText();
        console.log('🔍 [UNIFIED] Canonical text length:', canonicalText.length);

        // Initialize font metrics
        this.fontMetrics = this.getFontMetrics();

        // Mark as initialized
        this.isInitialized = true;
        console.log('🔍 [UNIFIED] Positioning strategy initialized:', {
            textLength: canonicalText.length,
            fontMetrics: this.fontMetrics
        });
    }

    /**
     * Wait for DOM elements to be available
     */
    async waitForElements() {
        return new Promise((resolve) => {
            const check = () => {
                if (this.container && this.container.textContent && this.container.textContent.trim()) {
                    console.log('🔍 [UNIFIED] DOM elements ready');
                    resolve();
                } else {
                    console.log('🔍 [UNIFIED] Waiting for DOM elements...');
                    setTimeout(check, 50);
                }
            };
            check();
        });
    }

    /**
     * Wait for font loading and layout stabilization
     */
    async waitForFontMetrics() {
        return new Promise((resolve) => {
            // Wait for fonts to load
            if (document.fonts && document.fonts.ready) {
                document.fonts.ready.then(() => {
                    // Additional wait for layout stabilization
                    setTimeout(() => {
                        console.log('🔍 [UNIFIED] Fonts loaded and layout stabilized');
                        resolve();
                    }, 200);
                });
            } else {
                // Fallback: wait a reasonable time
                setTimeout(() => {
                    console.log('🔍 [UNIFIED] Font loading fallback completed');
                    resolve();
                }, 800);
            }
        });
    }

        /**
     * Get canonical text (single source of truth)
     */
    getCanonicalText() {
        console.log('🔍 [UNIFIED] Getting canonical text');

        // First try to get from data-original-text attribute
        if (this.container.hasAttribute('data-original-text')) {
            const originalText = this.container.getAttribute('data-original-text');
            console.log('🔍 [UNIFIED] Using data-original-text:', originalText);
            // Clean any HTML markup that might have been stored
            const cleanText = originalText.replace(/<[^>]*>/g, '').trim();
            console.log('🔍 [UNIFIED] Cleaned text from data-original-text:', cleanText);
            return this.normalizeText(cleanText);
        }

        // Fallback to textContent
        const textContent = this.container.textContent || '';
        console.log('🔍 [UNIFIED] Using textContent:', textContent);
        return this.normalizeText(textContent);
    }

    /**
     * Normalize text for consistent positioning
     */
    normalizeText(text) {
        return text
            .replace(/\s+/g, ' ')  // Normalize whitespace
            .trim()                // Remove leading/trailing whitespace
            .replace(/[^\x20-\x7E]/g, ''); // Remove non-printable characters
    }

    /**
     * Get font metrics for positioning calculations
     */
    getFontMetrics() {
        return getFontMetrics(this.container);
    }

    /**
     * Create span from text selection using algorithm-based positioning only
     */
    createSpanFromSelection(selection) {
        if (!this.isInitialized) {
            console.error('🔍 [UNIFIED] Positioning strategy not initialized');
            return null;
        }

        const selectedText = selection.toString().trim();
        if (!selectedText) {
            console.warn('🔍 [UNIFIED] No text selected');
            return null;
        }

        console.log('🔍 [UNIFIED] Creating span from selection:', selectedText);

        // Get the canonical text - use stored original text if available
        let canonicalText = this.getCanonicalText();
        const textElement = document.getElementById('text-content');
        if (textElement) {
            const storedText = textElement.getAttribute('data-original-text');
            if (storedText) {
                canonicalText = storedText;
                console.log('🔍 [UNIFIED] Using stored original text for selection matching');
            }
        }

        // Find the selection in the canonical text
        const start = canonicalText.indexOf(selectedText);
        if (start === -1) {
            console.warn('🔍 [UNIFIED] Selected text not found in canonical text');
            return null;
        }

        const end = start + selectedText.length;

        return this.createSpanWithAlgorithm(start, end, selectedText);
    }

    /**
     * Create span using algorithm-based positioning
     */
    createSpanWithAlgorithm(start, end, text) {
        console.log('🔍 [UNIFIED] createSpanWithAlgorithm called:', { start, end, text });

        if (!this.isInitialized) {
            console.error('🔍 [UNIFIED] Positioning strategy not initialized');
            return null;
        }

        // Validate span boundaries
        const canonicalText = this.getCanonicalText();
        if (start < 0 || end > canonicalText.length || start >= end) {
            console.warn('🔍 [UNIFIED] Invalid span boundaries:', { start, end, textLength: canonicalText.length });
            return null;
        }

        console.log('🔍 [UNIFIED] About to call getTextPositions...');
        // Use browser's built-in text measurement instead of manual calculation
        const positions = this.getTextPositions(start, end, text);
        console.log('🔍 [UNIFIED] getTextPositions returned:', positions);

        if (!positions || positions.length === 0) {
            console.warn('🔍 [UNIFIED] Could not get text positions for span');
            return null;
        }

        // Create span object with color information
        const span = {
            id: `span_${start}_${end}_${Date.now()}`,
            start: start,
            end: end,
            text: text,
            label: 'unknown', // This will be set by the caller
            color: null // This will be set by the caller
        };

        console.log('🔍 [UNIFIED] About to call createOverlay...');
        // Create overlay using proper positioning
        const overlay = this.createOverlay(span, positions);
        console.log('🔍 [UNIFIED] createOverlay returned:', overlay);

        if (!overlay) {
            console.warn('🔍 [UNIFIED] Could not create overlay for span');
            return null;
        }

        console.log('🔍 [UNIFIED] Span created successfully:', { span, overlay });
        return { span, overlay, positions };
    }

    /**
     * Get text positions using browser's built-in measurement
     */
    getTextPositions(start, end, text) {
        console.log('🔍 [UNIFIED] getTextPositions called:', { start, end, text });

        // Get the text content element
        const textElement = document.getElementById('text-content');
        if (!textElement) {
            console.error('🔍 [UNIFIED] Text content element not found');
            return null;
        }

        // Get the actual text content - use stored original text if available
        let actualText = textElement.getAttribute('data-original-text');
        if (!actualText) {
            actualText = textElement.textContent || textElement.innerText || '';
        }
        console.log('🔍 [UNIFIED] Actual text content:', actualText);

        // Find the target text in the actual content
        const targetStart = actualText.indexOf(text);
        if (targetStart === -1) {
            console.warn('🔍 [UNIFIED] Target text not found in actual content');
            return null;
        }

        const targetEnd = targetStart + text.length;
        console.log('🔍 [UNIFIED] Target range:', { targetStart, targetEnd });

        // Create a range for the target text
        const range = document.createRange();

        // Get the text node inside text-content
        let textNode = textElement.firstChild;
        if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
            // Try to find a text node inside text-content
            textNode = Array.from(textElement.childNodes).find(
                node => node.nodeType === Node.TEXT_NODE
            );
            if (!textNode) {
                console.warn('🔍 [UNIFIED] No text node found in text-content');
                console.log('🔍 [UNIFIED] textElement childNodes:', Array.from(textElement.childNodes).map(n => ({ nodeType: n.nodeType, textContent: n.textContent?.substring(0, 50) })));
                return null;
            }
        }

        console.log('🔍 [UNIFIED] Found text node:', { nodeType: textNode.nodeType, textContent: textNode.textContent?.substring(0, 100) });

        // Ensure the text node content matches the actualText
        if (textNode.textContent !== actualText) {
            console.log('🔍 [UNIFIED] Text node content does not match actualText, updating...');
            console.log('🔍 [UNIFIED] Text node content:', textNode.textContent);
            console.log('🔍 [UNIFIED] Actual text:', actualText);
            textNode.textContent = actualText;
        }

        try {
            range.setStart(textNode, targetStart);
            range.setEnd(textNode, targetEnd);
            console.log('🔍 [UNIFIED] Range set successfully:', { start: targetStart, end: targetEnd });
        } catch (error) {
            console.error('🔍 [UNIFIED] Error setting range:', error);
            return null;
        }

        // Get the bounding rectangles
        const rects = range.getClientRects();
        console.log('🔍 [UNIFIED] Got bounding rects:', rects.length);

        if (rects.length === 0) {
            console.warn('🔍 [UNIFIED] No bounding rects returned');
            return null;
        }

        // Get the container's bounding rect for relative positioning
        const containerRect = textElement.getBoundingClientRect();
        console.log('🔍 [UNIFIED] Container rect:', containerRect);

        // Convert to position objects with relative coordinates
        const positions = Array.from(rects).map(rect => ({
            x: rect.left - containerRect.left,
            y: rect.top - containerRect.top,
            width: rect.width,
            height: rect.height
        }));

        console.log('🔍 [UNIFIED] Converted positions (relative to text-content):', positions);
        return positions;
    }

    /**
     * Create overlay using proper positioning
     */
    createOverlay(span, positions) {
        console.log('🔍 [OVERLAY] createOverlay called with span:', span, 'positions:', positions);

        if (!positions || positions.length === 0) {
            console.warn('🔍 [OVERLAY] No positions provided for overlay');
            return null;
        }

        // Create the main overlay container
        const overlay = document.createElement('div');
        overlay.className = 'span-overlay-pure';
        overlay.dataset.annotationId = span.id;
        overlay.dataset.start = span.start;
        overlay.dataset.end = span.end;
        overlay.dataset.label = span.label;

        // Set positioning relative to text-content container
        overlay.style.position = 'absolute';
        overlay.style.pointerEvents = 'none';
        overlay.style.zIndex = '1000';

        // Create highlight segments for each position
        positions.forEach((pos, index) => {
            const segment = document.createElement('div');
            segment.className = 'span-highlight-segment';
            segment.style.position = 'absolute';
            segment.style.left = `${pos.x}px`;
            segment.style.top = `${pos.y}px`;
            segment.style.width = `${pos.width}px`;
            segment.style.height = `${pos.height}px`;
            segment.style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
            segment.style.border = '1px solid rgba(255, 255, 0, 0.8)';
            segment.style.borderRadius = '2px';
            segment.style.pointerEvents = 'none';
            overlay.appendChild(segment);
        });

        // Create label
        const label = document.createElement('div');
        label.className = 'span-label';
        label.textContent = span.label;
        label.style.position = 'absolute';
        label.style.left = `${positions[0].x}px`;
        label.style.top = `${positions[0].y - 20}px`;
        label.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        label.style.color = 'white';
        label.style.padding = '2px 6px';
        label.style.borderRadius = '3px';
        label.style.fontSize = '12px';
        label.style.pointerEvents = 'none';
        overlay.appendChild(label);

        // Create delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'span-delete-btn';
        deleteBtn.textContent = '×';
        deleteBtn.style.position = 'absolute';
        deleteBtn.style.left = `${positions[0].x + positions[0].width}px`;
        deleteBtn.style.top = `${positions[0].y - 20}px`;
        deleteBtn.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
        deleteBtn.style.color = 'white';
        deleteBtn.style.border = 'none';
        deleteBtn.style.borderRadius = '50%';
        deleteBtn.style.width = '20px';
        deleteBtn.style.height = '20px';
        deleteBtn.style.fontSize = '14px';
        deleteBtn.style.cursor = 'pointer';
        deleteBtn.style.pointerEvents = 'auto';
        deleteBtn.onclick = () => this.deleteSpan(span.id);
        overlay.appendChild(deleteBtn);

        console.log('🔍 [OVERLAY] Overlay created successfully with:', {
            segments: positions.length,
            label: span.label,
            labelText: label.textContent,
            deleteButton: deleteBtn.textContent,
            totalChildren: overlay.children.length
        });

        return overlay;
    }

    /**
     * Create span from API data (for rendering existing annotations)
     */
    createSpanFromAPI(spanData) {
        if (!this.isInitialized) {
            console.error('🔍 [UNIFIED] Positioning strategy not initialized');
            return null;
        }

        const { start, end, text } = spanData;
        console.log('🔍 [UNIFIED] Creating span from API:', { start, end, text });

        return this.createSpanWithAlgorithm(start, end, text);
    }

    /**
     * Validate that a span can be positioned correctly
     */
    validateSpan(span) {
        if (!this.isInitialized) {
            return false;
        }

        const { start, end, text } = span;

        // Check range validity
        if (start >= end || start < 0 || end > this.canonicalText.length) {
            return false;
        }

        // Check text consistency
        const coveredText = this.canonicalText.substring(start, end);
        return coveredText === text;
    }

    /**
     * Get text at specific positions
     */
    getTextAtPosition(start, end) {
        if (!this.isInitialized) {
            return null;
        }

        if (start < 0 || end > this.canonicalText.length || start >= end) {
            return null;
        }

        return this.canonicalText.substring(start, end);
    }
}

/**
 * Frontend Span Manager for Potato Annotation Platform
 * Handles span annotation rendering, interaction, and API communication
 */

class SpanManager {
    constructor() {
        console.log('[DEEPDEBUG] SpanManager constructor called');

        // Core state
        this.annotations = {spans: []};
        this.colors = {};
        this.selectedLabel = null;
        this.currentSchema = null; // Track the current schema
        this.isInitialized = false;
        this.currentInstanceId = null;
        this.lastKnownInstanceId = null;

        // Unified positioning strategy
        this.positioningStrategy = null;

        // Debug tracking
        this.debugState = {
            constructorCalls: 0,
            initializeCalls: 0,
            loadAnnotationsCalls: 0,
            onInstanceChangeCalls: 0,
            clearAllStateCalls: 0,
            renderSpansCalls: 0,
            lastInstanceIdFromServer: null,
            lastInstanceIdFromDOM: null,
            lastOverlayCount: 0,
            stateTransitions: []
        };

        this.debugState.constructorCalls++;
        this.debugState.stateTransitions.push({
            timestamp: new Date().toISOString(),
            action: 'constructor',
            currentInstanceId: this.currentInstanceId,
            lastKnownInstanceId: this.lastKnownInstanceId
        });

        // Retry logic for robustness
        this.retryCount = 0;
        this.maxRetries = 3;

        // Aggressive state clearing on construction
        this.clearAllStateAndOverlays();

        console.log('[DEEPDEBUG] SpanManager constructor completed', {
            debugState: this.debugState,
            currentInstanceId: this.currentInstanceId,
            isInitialized: this.isInitialized
        });
    }

    /**
     * Deep debug logging utility
     */
    logDebugState(action, extraData = {}) {
        const state = {
            timestamp: new Date().toISOString(),
            action: action,
            currentInstanceId: this.currentInstanceId,
            lastKnownInstanceId: this.lastKnownInstanceId,
            isInitialized: this.isInitialized,
            annotationsCount: this.annotations?.spans?.length || 0,
            debugState: { ...this.debugState },
            ...extraData
        };

        console.log(`[DEEP DEBUG] ${action}:`, state);
        this.debugState.stateTransitions.push(state);

        // Keep only last 50 transitions to avoid memory bloat
        if (this.debugState.stateTransitions.length > 50) {
            this.debugState.stateTransitions = this.debugState.stateTransitions.slice(-50);
        }
    }

    /**
     * Alternative workflow: Fetch current instance ID from server before any operations
     * This ensures we always have the correct instance ID, even if DOM is stale
     */
    async fetchCurrentInstanceIdFromServer() {
        try {
            console.log('[DEEP DEBUG] fetchCurrentInstanceIdFromServer called');

            const response = await fetch('/api/current_instance');
            if (!response.ok) {
                throw new Error(`Failed to fetch current instance: ${response.status}`);
            }

            const data = await response.json();
            const serverInstanceId = data.instance_id;

            console.log('[DEEP DEBUG] Server returned instance ID:', serverInstanceId);

            // Update debug state
            this.debugState.lastInstanceIdFromServer = serverInstanceId;

            // Check if this is different from what we have
            if (this.currentInstanceId !== serverInstanceId) {
                console.log('[DEEP DEBUG] Instance ID mismatch detected!', {
                    currentInstanceId: this.currentInstanceId,
                    serverInstanceId: serverInstanceId,
                    lastKnownInstanceId: this.lastKnownInstanceId
                });

                // Force state reset if instance ID changed
                if (this.currentInstanceId !== null) {
                    console.log('[DEEP DEBUG] Instance ID changed, forcing state reset');
                    this.clearAllStateAndOverlays();
                }
            }

            this.currentInstanceId = serverInstanceId;
            this.lastKnownInstanceId = serverInstanceId;

            this.logDebugState('fetchCurrentInstanceIdFromServer', {
                serverInstanceId: serverInstanceId,
                previousInstanceId: this.currentInstanceId
            });

            return serverInstanceId;
        } catch (error) {
            console.error('[DEEP DEBUG] Error fetching current instance ID:', error);
            return null;
        }
    }

    /**
     * Initialize the span manager
     */
    async initialize() {
        console.log('[DEEP DEBUG] initialize called');
        this.debugState.initializeCalls++;

        try {
            // Step 1: Fetch current instance ID from server first
            const serverInstanceId = await this.fetchCurrentInstanceIdFromServer();
            if (!serverInstanceId) {
                console.error('[DEEP DEBUG] Failed to get server instance ID during initialization');
                return false;
            }

            // Step 2: Initialize unified positioning strategy
            const textContent = document.getElementById('text-content');
            if (textContent) {
                console.log('[DEEP DEBUG] Creating unified positioning strategy');
                this.positioningStrategy = new UnifiedPositioningStrategy(textContent);
                console.log('[DEEP DEBUG] Positioning strategy created, initializing...');
                try {
                    await this.positioningStrategy.initialize();
                    console.log('[DEEP DEBUG] Unified positioning strategy initialized successfully');
                } catch (error) {
                    console.error('[DEEP DEBUG] Failed to initialize positioning strategy:', error);
                }
            } else {
                console.error('[DEEP DEBUG] Text content element not found');
            }

            // Step 3: Load schemas from server API
            await this.loadSchemas();

            // Step 4: Load colors
            await this.loadColors();

            // Step 5: Setup event listeners
            this.setupEventListeners();

            // Step 6: Load annotations for the verified instance ID
            await this.loadAnnotations(serverInstanceId);

            this.isInitialized = true;

            this.logDebugState('initialize_completed', {
                serverInstanceId: serverInstanceId,
                isInitialized: this.isInitialized,
                currentSchema: this.currentSchema
            });

            console.log('[DEEPDEBUG] SpanManager initialization completed successfully');
            return true;
        } catch (error) {
            console.error('[DEEP DEBUG] SpanManager initialization failed:', error);
            this.isInitialized = false;
            return false;
        }
    }

    /**
     * Load color scheme from API
     */
    async loadColors() {
        try {
            const response = await fetch('/api/colors');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.colors = await response.json();
            console.log('SpanManager: Colors loaded:', this.colors);
        } catch (error) {
            console.error('SpanManager: Error loading colors:', error);
            // Fallback colors
            this.colors = {
                'positive': '#d4edda',
                'negative': '#f8d7da',
                'neutral': '#d1ecf1',
                'span': '#ffeaa7'
            };
        }
    }

    /**
     * Load schema information from server API
     */
    async loadSchemas() {
        try {
            const response = await fetch('/api/schemas');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.schemas = await response.json();
            console.log('SpanManager: Schemas loaded from server:', this.schemas);

            // Set the first schema as default if no schema is currently set
            if (!this.currentSchema && Object.keys(this.schemas).length > 0) {
                this.currentSchema = Object.keys(this.schemas)[0];
                console.log('SpanManager: Set default schema:', this.currentSchema);
            }

            return this.schemas;
        } catch (error) {
            console.error('SpanManager: Error loading schemas:', error);
            // Fallback to extracting from HTML forms
            return this.extractSchemaFromForms();
        }
    }

    /**
     * Extract schema from HTML forms (fallback method)
     */
    extractSchemaFromForms() {
        // Look for span annotation forms and extract schema information
        const spanForms = document.querySelectorAll('.annotation-form.span');
        if (spanForms.length > 0) {
            // Get the schema from the first span form's fieldset
            const firstSpanForm = spanForms[0];
            const fieldset = firstSpanForm.querySelector('fieldset');
            if (fieldset && fieldset.getAttribute('schema')) {
                const schema = fieldset.getAttribute('schema');
                console.log('SpanManager: Extracted schema from forms:', schema);
                return schema;
            }
        }
        return null;
    }

    /**
     * Setup event listeners for span interaction
     */
    setupEventListeners() {
        // Text selection handling
        const textContainer = document.getElementById('instance-text');
        const textContent = document.getElementById('text-content');
        if (textContainer) {
            textContainer.addEventListener('mouseup', () => this.handleTextSelection());
            textContainer.addEventListener('keyup', () => this.handleTextSelection());
        }
        if (textContent) {
            textContent.addEventListener('mouseup', () => this.handleTextSelection());
            textContent.addEventListener('keyup', () => this.handleTextSelection());
        }

        // DEBUG: Global mouseup event listener
        document.addEventListener('mouseup', (e) => {
            console.log('DEBUG: Global mouseup event fired on', e.target ? e.target.id : '(no id)', 'class:', e.target ? e.target.className : '(no class)');
        });

        // Span deletion
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('span-delete')) {
                e.stopPropagation();
                const annotationId = e.target.closest('.span-highlight').dataset.annotationId;
                this.deleteSpan(annotationId);
            }
        });
    }

        /**
     * Select a label for annotation
     */
    selectLabel(label, schema = null) {
        console.log('🔍 [DEBUG] SpanManager.selectLabel() called with:', { label, schema });

        // Don't interfere with checkbox state management - let the onlyOne function handle it
        // The onlyOne function already manages the checkbox state correctly
        console.log('🔍 [DEBUG] SpanManager.selectLabel() - Skipping checkbox state management, letting onlyOne handle it');

        this.selectedLabel = label;
        if (schema) {
            this.currentSchema = schema;
        }
        console.log('SpanManager: Selected label:', label, 'schema:', this.currentSchema);
    }

    /**
     * Get the currently selected label from checkbox inputs
     */
    getSelectedLabel() {
        // Check if any span checkbox is checked
        const checkedCheckbox = document.querySelector('.annotation-form.span input[type="checkbox"]:checked');
        if (checkedCheckbox) {
            // Extract the actual label text from the checkbox ID
            // Checkbox ID format: "emotion_spans_positive", "emotion_spans_negative", etc.
            const checkboxId = checkedCheckbox.id;
            const parts = checkboxId.split('_');
            if (parts.length >= 3) {
                // Format: scheme_annotationType_label (e.g., "emotion_spans_positive")
                const labelText = parts[2]; // Get the label part (third part)
                console.log('SpanManager: Extracted label text from checkbox ID:', { checkboxId, labelText });
                return labelText;
            } else if (parts.length >= 2) {
                // Fallback for two-part format: scheme_label (e.g., "emotion_positive")
                const labelText = parts[1]; // Get the label part (second part)
                console.log('SpanManager: Extracted label text from checkbox ID (two-part format):', { checkboxId, labelText });
                return labelText;
            }
            // Fallback to value if ID parsing fails
            console.warn('SpanManager: Could not parse label from checkbox ID, using value:', checkboxId);
            return checkedCheckbox.value;
        }
        return this.selectedLabel;
    }

    /**
     * Load annotations for current instance
     */
    async loadAnnotations(instanceId) {
        console.log('🔍 [NAVIGATION] loadAnnotations called with instanceId:', instanceId);

        try {
            // Clean up any corrupted data-original-text first
            this.cleanupDataOriginalText();

            // Step 1: Verify instance ID with server
            const serverInstanceId = await this.fetchCurrentInstanceIdFromServer();
            if (serverInstanceId !== instanceId) {
                console.warn('🔍 [NAVIGATION] Instance ID mismatch detected:', {
                    requestedInstanceId: instanceId,
                    serverInstanceId: serverInstanceId
                });
                instanceId = serverInstanceId;
            }

            // Step 2: Check if server-rendered spans are already present
            const textContent = document.getElementById('text-content');
            const existingSpans = textContent ? textContent.querySelectorAll('.span-highlight') : [];
            const hasServerRenderedSpans = existingSpans.length > 0;

            console.log('🔍 [NAVIGATION] Server-rendered spans check:', {
                existingSpansCount: existingSpans.length,
                hasServerRenderedSpans: hasServerRenderedSpans,
                textContentHTML: textContent ? textContent.innerHTML.substring(0, 200) + '...' : 'null'
            });

            // Check for text duplication before processing
            this.detectTextDuplication();

            // Step 3: Fetch annotations from server
            const response = await fetch(`/api/spans/${instanceId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    // No annotations yet
                    this.annotations = {spans: []};
                    console.log('🔍 [NAVIGATION] No annotations found (404)');

                    // Only clear and render if no server-rendered spans exist
                    if (!hasServerRenderedSpans) {
                        this.clearAllStateAndOverlays();
                        this.renderSpans();
                    }
                    return Promise.resolve();
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Store the full API response, not just the spans array
            const responseText = await response.text();
            let responseData;
            try {
                responseData = JSON.parse(responseText);
            } catch (error) {
                console.error('🔍 [NAVIGATION] JSON parse error:', error);
                throw new Error(`Failed to parse JSON response: ${error.message}`);
            }

            this.annotations = responseData;
            console.log('🔍 [NAVIGATION] Annotations loaded:', {
                instanceId: instanceId,
                annotationsCount: this.annotations?.spans?.length || 0,
                originalText: this.annotations?.text || 'No text'
            });

            // Store the original text from the backend for consistent positioning
            if (this.annotations && this.annotations.text) {
                // Store the original text in the text content element for positioning calculations
                if (textContent) {
                    // Ensure we store only plain text, not HTML markup
                    const plainText = this.annotations.text.replace(/<[^>]*>/g, '').trim();
                    textContent.setAttribute('data-original-text', plainText);
                    console.log('🔍 [NAVIGATION] Stored clean original text:', plainText);
                }

                // Also store in the global currentInstance for compatibility
                if (window.currentInstance) {
                    window.currentInstance.text = this.annotations.text;
                }
            }

            // Auto-set the schema from the first span if available
            if (this.annotations.spans && this.annotations.spans.length > 0) {
                const firstSpan = this.annotations.spans[0];
                if (firstSpan.schema && !this.currentSchema) {
                    this.currentSchema = firstSpan.schema;
                }
            }

            // Step 4: Handle rendering based on whether server-rendered spans exist
            if (hasServerRenderedSpans) {
                console.log('🔍 [NAVIGATION] Server-rendered spans detected, preserving them');
                // Use the API data for correct positioning instead of calculating from DOM
                this.updateInternalStateFromAPI();
                // Still need to render overlays even when server-rendered spans exist
                console.log('🔍 [NAVIGATION] Rendering overlays for server-rendered spans');
                this.renderSpans();
            } else {
                console.log('🔍 [NAVIGATION] No server-rendered spans, rendering normally');
                this.renderSpans();
            }

            // Check for text duplication after processing
            this.detectTextDuplication();

        } catch (error) {
            console.error('🔍 [NAVIGATION] Error loading annotations:', error);
            throw error;
        }
    }

    /**
     * Render all spans in the text container using interval-based approach
     * This method properly handles partial overlaps by using position-based rendering
     */
    renderSpans() {
        console.log('🔍 [RENDER] renderSpans called');

        // Check for text duplication before rendering
        this.detectTextDuplication();

        const textContainer = document.getElementById('text-container');
        const textContent = document.getElementById('text-content');
        const spanOverlays = document.getElementById('span-overlays');

        if (!textContent) {
            console.error('🔍 [RENDER] text-content element not found');
            return;
        }

        if (!spanOverlays) {
            console.error('🔍 [RENDER] span-overlays element not found');
            return;
        }

        this._renderSpansInternal(textContainer, textContent, spanOverlays);

        // Check for text duplication after rendering
        this.detectTextDuplication();
    }

    /**
     * Internal method to render spans once DOM elements are confirmed available
     */
    _renderSpansInternal(textContainer, textContent, spanOverlays) {
        console.log('🔍 [RENDER] _renderSpansInternal called');
        console.log('🔍 [RENDER] Current textContent HTML before processing:', textContent.innerHTML.substring(0, 300) + '...');

        // Clean up any corrupted data-original-text first
        this.cleanupDataOriginalText();

        const spans = this.getSpans();
        console.log('🔍 [RENDER] Spans to render:', spans?.length || 0);

        // Clear existing overlays
        spanOverlays.innerHTML = '';

        // Check if server-rendered spans are already present
        const existingSpans = textContent.querySelectorAll('.span-highlight');
        const hasServerRenderedSpans = existingSpans.length > 0;

        console.log('🔍 [RENDER] Server-rendered spans check:', {
            existingSpansCount: existingSpans.length,
            hasServerRenderedSpans: hasServerRenderedSpans
        });

        if (!spans || spans.length === 0) {
            if (!hasServerRenderedSpans) {
                // Only display plain text if no server-rendered spans exist
                const originalText = window.currentInstance?.text || '';
                textContent.textContent = originalText;
                // Store the original text for positioning calculations
                textContent.setAttribute('data-original-text', originalText);
                console.log('🔍 [RENDER] No spans to render, displaying original text:', originalText);
            } else {
                console.log('🔍 [RENDER] No spans to render, but server-rendered spans exist - preserving them');
                // Store the original text for positioning calculations without changing the display
                const originalText = window.currentInstance?.text || '';
                textContent.setAttribute('data-original-text', originalText);
            }
            console.log('🔍 [RENDER] Final textContent HTML after no spans:', textContent.innerHTML.substring(0, 300) + '...');
            return;
        }

        // Always set text content to original text for positioning calculations
        // Use the original text from the backend API if available, otherwise fall back to window.currentInstance
        let text = '';
        if (this.annotations && this.annotations.text) {
            // Use the original text from the backend API
            text = this.annotations.text;
            console.log('🔍 [RENDER] Using original text from backend API:', text);
        } else if (window.currentInstance && window.currentInstance.text) {
            // Fallback to window.currentInstance
            text = window.currentInstance.text;
            console.log('🔍 [RENDER] Using text from window.currentInstance:', text);
        } else {
            console.warn('🔍 [RENDER] No text available for positioning');
            text = '';
        }

        // Store the original text for positioning calculations
        textContent.setAttribute('data-original-text', text);

        if (!hasServerRenderedSpans) {
            // Display text in text content layer only if no server-rendered spans exist
            textContent.textContent = text;
            console.log('🔍 [RENDER] Set text content to:', text);
        } else {
            // For server-rendered spans, preserve the existing HTML structure
            // Don't overwrite the HTML - just store the original text for positioning
            console.log('🔍 [RENDER] Preserving server-rendered HTML structure');
            // Ensure the text content is clean for positioning calculations
            const cleanText = text.replace(/<[^>]*>/g, '').trim();
            textContent.setAttribute('data-original-text', cleanText);
        }

        console.log('🔍 [RENDER] TextContent HTML after text processing:', textContent.innerHTML.substring(0, 300) + '...');

        // Sort spans by start position for consistent rendering
        const sortedSpans = [...spans].sort((a, b) => a.start - b.start);

        // Calculate overlap layers for visual styling
        const overlapDataArray = this.calculateOverlapDepths(sortedSpans);

        // Convert overlap data array to a Map for efficient lookup
        const overlapDataMap = new Map();
        overlapDataArray.forEach(data => {
            const spanKey = `${data.span.start}-${data.span.end}`;
            overlapDataMap.set(spanKey, {
                depth: data.depth,
                heightMultiplier: data.heightMultiplier
            });
        });

        // Render each span as an overlay
        console.log('🔍 [RENDER] About to render', sortedSpans.length, 'spans');
        sortedSpans.forEach((span, index) => {
            console.log(`🔍 [RENDER] Rendering span ${index}:`, span);
            this.renderSpanOverlay(span, index, textContent, spanOverlays, overlapDataMap);
        });

        // Apply overlap styling
        const spanElements = spanOverlays.querySelectorAll('.span-highlight');
        this.applyOverlapStyling(spanElements, overlapDataArray);

        console.log('🔍 [RENDER] Final textContent HTML after rendering:', textContent.innerHTML.substring(0, 300) + '...');
        console.log('🔍 [RENDER] Overlays created:', spanOverlays.children.length);
    }

    /**
     * Create a span element with proper styling and event handlers
     */
    createSpanElement(span) {
        const spanElement = document.createElement('span');
        spanElement.className = 'annotation-span';
        spanElement.dataset.spanId = span.id;
        spanElement.dataset.start = span.start;
        spanElement.dataset.end = span.end;
        spanElement.dataset.label = span.label;

        // Apply the correct color for this label
        const backgroundColor = this.getSpanColor(span.label);
        if (backgroundColor) {
            spanElement.style.backgroundColor = backgroundColor;
        }

        // Add delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'span-delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete span';
        deleteBtn.style.position = 'absolute';
        deleteBtn.style.left = `${span.start}px`;
        deleteBtn.style.top = `${span.start}px`;
        deleteBtn.style.backgroundColor = '#dc3545';
        deleteBtn.style.color = 'white';
        deleteBtn.style.border = 'none';
        deleteBtn.style.borderRadius = '50%';
        deleteBtn.style.width = '18px';
        deleteBtn.style.height = '18px';
        deleteBtn.style.fontSize = '14px';
        deleteBtn.style.cursor = 'pointer';
        deleteBtn.style.pointerEvents = 'auto';
        deleteBtn.style.zIndex = '1002';
        deleteBtn.style.display = 'flex';
        deleteBtn.style.alignItems = 'center';
        deleteBtn.style.justifyContent = 'center';
        deleteBtn.style.fontWeight = 'bold';
        deleteBtn.style.lineHeight = '1';
        deleteBtn.style.transition = 'all 0.2s ease';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            if (window.spanManager) {
                window.spanManager.deleteSpan(span.id);
            }
        };
        spanElement.appendChild(deleteBtn);

        // Add label display
        const labelSpan = document.createElement('span');
        labelSpan.className = 'span-label';
        labelSpan.textContent = span.label;
        spanElement.appendChild(labelSpan);

        return spanElement;
    }

    /**
     * Render a span as an overlay using unified positioning strategy
     */
    renderSpanOverlay(span, layerIndex, textContent, spanOverlays, overlapData) {
        console.log('🔍 [OVERLAY] renderSpanOverlay called for span:', span);

        // Use unified positioning strategy
        if (!this.positioningStrategy || !this.positioningStrategy.isInitialized) {
            console.error('🔍 [OVERLAY] Positioning strategy not available');
            return;
        }

        // Validate span using unified strategy
        if (!this.positioningStrategy.validateSpan(span)) {
            console.warn('🔍 [OVERLAY] Invalid span for rendering:', span);
            return;
        }

        // Create span using algorithm-based positioning
        const spanResult = this.positioningStrategy.createSpanWithAlgorithm(span.start, span.end, span.text);
        if (!spanResult) {
            console.warn('🔍 [OVERLAY] Could not create span result for:', span);
            return;
        }

        // Get the overlay from the result
        const overlay = spanResult.overlay;
        if (!overlay) {
            console.warn('🔍 [OVERLAY] Could not create overlay for span', span);
            return;
        }

        console.log('🔍 [OVERLAY] Overlay created successfully:', {
            spanId: span.id,
            label: span.label,
            start: span.start,
            end: span.end,
            overlayClass: overlay.className,
            overlayChildren: overlay.children.length
        });

        // Apply overlap styling if needed
        const spanKey = `${span.start}-${span.end}`;
        const overlapInfo = overlapData.get(spanKey) || { depth: 0, heightMultiplier: 1.0 };

        if (overlapInfo.depth > 0) {
            overlay.classList.add('span-overlap');
            overlay.classList.add(`overlap-depth-${overlapInfo.depth}`);
            overlay.style.setProperty('--overlap-depth', overlapInfo.depth);
            overlay.style.setProperty('--max-depth', Math.max(...Array.from(overlapData.values()).map(d => d.depth)));
        }

        // Apply the correct color for this label
        const backgroundColor = this.getSpanColor(span.label);
        if (backgroundColor) {
            overlay.style.setProperty('--span-color', backgroundColor);
            // Also set the color directly on the overlay for immediate effect
            overlay.style.backgroundColor = backgroundColor;
        }

        // Set z-index
        overlay.style.setProperty('--span-z-index', 10 + overlapInfo.depth);

        // Add overlay to container
        spanOverlays.appendChild(overlay);
        console.log('🔍 [OVERLAY] Overlay added to container successfully');
    }

    /**
     * Create an overlay span for overlapping annotations (legacy method - kept for compatibility)
     */
    createOverlaySpan(span, layerIndex) {
        const overlaySpan = document.createElement('span');
        overlaySpan.className = 'annotation-span overlay-span';
        overlaySpan.dataset.spanId = span.id;
        overlaySpan.dataset.start = span.start;
        overlaySpan.dataset.end = span.end;
        overlaySpan.dataset.label = span.label;

        // Apply the correct color for this label
        const backgroundColor = this.getSpanColor(span.label);
        if (backgroundColor) {
            overlaySpan.style.backgroundColor = backgroundColor;
        }

        // Position the overlay span
        overlaySpan.style.position = 'absolute';
        overlaySpan.style.top = '0';
        overlaySpan.style.left = '0';
        overlaySpan.style.right = '0';
        overlaySpan.style.bottom = '0';
        overlaySpan.style.zIndex = layerIndex + 1;
        // CSS will handle pointer events for overlay spans

        // Add delete button (positioned absolutely)
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'span-delete-btn overlay-delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete span';
        deleteBtn.style.position = 'absolute';
        deleteBtn.style.top = '-20px';
        deleteBtn.style.right = '0';
        deleteBtn.style.zIndex = layerIndex + 2;
        deleteBtn.style.pointerEvents = 'auto'; // Allow clicks on delete button
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            this.deleteSpan(span.id);
        };
        overlaySpan.appendChild(deleteBtn);

        // Add label display (always visible for overlay spans)
        const labelSpan = document.createElement('span');
        labelSpan.className = 'span-label overlay-label';
        labelSpan.textContent = span.label;
        // Make label always visible for overlay spans
        labelSpan.style.position = 'absolute';
        labelSpan.style.top = '-25px';
        labelSpan.style.left = '0';
        labelSpan.style.zIndex = layerIndex + 2;
        labelSpan.style.display = 'block'; // Always show for overlay spans
        labelSpan.style.pointerEvents = 'auto';
        overlaySpan.appendChild(labelSpan);

        return overlaySpan;
    }

    /**
     * Handle text selection and create annotation using pure CSS approach
     */
    handleTextSelection() {
        console.log('🔍 [UNIFIED] handleTextSelection METHOD CALLED!');
        const selection = window.getSelection();
        console.log('🔍 [UNIFIED] handleTextSelection entered, selection:', selection ? selection.toString() : '(none)', 'rangeCount:', selection ? selection.rangeCount : '(none)', 'isCollapsed:', selection ? selection.isCollapsed : '(none)');
        if (!selection.rangeCount || selection.isCollapsed) return;

        const selectedLabel = this.getSelectedLabel();
        console.log('🔍 [UNIFIED] Selected label:', selectedLabel);
        if (!selectedLabel) {
            this.showStatus('Please select a label first', 'error');
            return;
        }

        // Use unified positioning strategy
        console.log('🔍 [UNIFIED] Checking positioning strategy:', {
            positioningStrategyExists: !!this.positioningStrategy,
            positioningStrategyType: this.positioningStrategy ? this.positioningStrategy.constructor.name : 'none',
            positioningStrategyInitialized: this.positioningStrategy ? this.positioningStrategy.isInitialized : 'none'
        });

        if (!this.positioningStrategy || !this.positioningStrategy.isInitialized) {
            console.error('🔍 [UNIFIED] Positioning strategy not available');
            this.showStatus('Positioning system not ready', 'error');
            this.clearTextSelection();
            return;
        }

        // Create span using algorithm-based positioning only
        console.log('🔍 [UNIFIED] About to call createSpanFromSelection...');
        console.log('🔍 [UNIFIED] Positioning strategy object:', this.positioningStrategy);
        console.log('🔍 [UNIFIED] createSpanFromSelection method exists:', typeof this.positioningStrategy.createSpanFromSelection);
        const spanResult = this.positioningStrategy.createSpanFromSelection(selection);
        console.log('🔍 [UNIFIED] Span result from positioning strategy:', spanResult);
        if (!spanResult) {
            console.error('🔍 [UNIFIED] Failed to create span from selection');
            this.showStatus('Failed to create span', 'error');
            this.clearTextSelection();
            return;
        }

        // Extract span data from the result
        const span = spanResult.span;
        const overlay = spanResult.overlay;
        console.log('🔍 [UNIFIED] Span created successfully:', {
            text: span.text,
            start: span.start,
            end: span.end,
            label: selectedLabel
        });

        // Clear selection immediately to prevent issues
        this.clearTextSelection();

        // Set the label and color for the span
        span.label = selectedLabel;
        span.color = this.getSpanColor(selectedLabel);

        // Update the overlay with the correct label and color
        if (overlay) {
            overlay.dataset.label = selectedLabel;
            const segments = overlay.querySelectorAll('.span-highlight-segment');
            segments.forEach(segment => {
                segment.style.backgroundColor = span.color || 'rgba(255, 234, 167, 0.4)';
                segment.style.border = `1px solid ${span.color ? span.color.replace('66', '') : 'rgba(255, 193, 7, 0.3)'}`;
            });

            const label = overlay.querySelector('.span-label');
            if (label) {
                label.textContent = selectedLabel;
            }
        }

        // Add the overlay to the DOM immediately for visual feedback
        if (overlay) {
            const spanOverlaysContainer = document.getElementById('span-overlays');
            if (spanOverlaysContainer) {
                spanOverlaysContainer.appendChild(overlay);
                console.log('🔍 [UNIFIED] Added overlay to span-overlays container for immediate visual feedback');
                console.log('🔍 [UNIFIED] Overlay element details:', {
                    className: overlay.className,
                    dataset: overlay.dataset,
                    children: overlay.children.length,
                    parent: overlay.parentElement ? overlay.parentElement.id : 'none'
                });
            } else {
                console.error('🔍 [UNIFIED] span-overlays container not found for overlay');
            }
        } else {
            console.error('🔍 [UNIFIED] No overlay to add to DOM');
        }

        // Create annotation via API
        this.createAnnotation(span.text, span.start, span.end, selectedLabel)
            .then(result => {
                console.log('🔍 [UNIFIED] Annotation creation successful:', result);
                // Update the span ID with the server-generated ID
                if (result && result.id && overlay) {
                    span.id = result.id;
                    overlay.dataset.annotationId = result.id;
                }
            })
            .catch(error => {
                console.error('🔍 [UNIFIED] Annotation creation failed:', error);
                // Remove the overlay if annotation creation failed
                if (overlay && overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
                this.showStatus('Failed to save annotation', 'error');
            });
    }

    /**
     * Get the character position within a text node
     * This is used for converting DOM positions to character offsets
     */
    getTextPosition(container, node, offset) {
        if (!container || !node) {
            console.error('SpanManager: getTextPosition called with null container or node');
            return null;
        }

        // Ensure we're working with the correct container
        if (node.parentElement !== container) {
            console.error('SpanManager: Node parent does not match container', {
                nodeParent: node.parentElement?.id || 'null',
                containerId: container.id || 'null'
            });
            return null;
        }

        // Ensure we have a text node
        if (node.nodeType !== Node.TEXT_NODE) {
            console.error('SpanManager: Node is not a text node', {
                nodeType: node.nodeType,
                nodeName: node.nodeName
            });
            return null;
        }

        // Validate offset
        if (offset < 0 || offset > node.textContent.length) {
            console.error('SpanManager: Invalid offset', {
                offset: offset,
                textLength: node.textContent.length
            });
            return null;
        }

        return offset;
    }

    /**
     * Calculate position in original text from DOM position (legacy method - kept for compatibility)
     * This is a more robust implementation that works with rendered spans
     */
    getOriginalTextPosition(container, node, offset) {
        // Get the original text from the global variable
        let originalText;
        if (window.currentInstance && window.currentInstance.text) {
            originalText = window.currentInstance.text;
        } else {
            // Fallback to container text content
            originalText = container.textContent || container.innerText;
        }

        if (!originalText) {
            console.warn('SpanManager: No original text available');
            return 0;
        }

        // Create a tree walker to traverse text nodes
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let currentNode;
        let textSoFar = '';
        let foundNode = false;

        // Walk through text nodes to find our target node
        while (currentNode = walker.nextNode()) {
            // Skip text nodes that belong to UI elements (delete buttons and labels)
            const parent = currentNode.parentElement;
            if (parent && (
                parent.classList.contains('span-delete-btn') ||
                parent.classList.contains('span-label') ||
                parent.closest('.span-delete-btn') ||
                parent.closest('.span-label')
            )) {
                continue; // Skip this text node
            }

            if (currentNode === node) {
                // Found our target node, add the text up to the offset
                textSoFar += currentNode.textContent.substring(0, offset);
                foundNode = true;
                break;
            }
            // Add the full text of this node
            textSoFar += currentNode.textContent;
        }

        if (!foundNode) {
            console.warn('SpanManager: Target node not found in DOM walk, attempting fallback');

            // Fallback: try to find the node by traversing the DOM tree
            const allTextNodes = [];
            const fallbackWalker = document.createTreeWalker(
                container,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let fallbackNode;
            while (fallbackNode = fallbackWalker.nextNode()) {
                const parent = fallbackNode.parentElement;
                if (parent && (
                    parent.classList.contains('span-delete-btn') ||
                    parent.classList.contains('span-label') ||
                    parent.closest('.span-delete-btn') ||
                    parent.closest('.span-label')
                )) {
                    continue;
                }
                allTextNodes.push(fallbackNode);
            }

            // Try to find the node in our collected text nodes
            const nodeIndex = allTextNodes.indexOf(node);
            if (nodeIndex !== -1) {
                // Calculate position based on previous text nodes
                for (let i = 0; i < nodeIndex; i++) {
                    textSoFar += allTextNodes[i].textContent;
                }
                textSoFar += node.textContent.substring(0, offset);
                foundNode = true;
            }
        }

        if (!foundNode) {
            console.warn('SpanManager: Target node not found in DOM walk, using fallback position');
            return 0;
        }

        // The length of textSoFar gives us the offset in the original text
        const calculatedOffset = textSoFar.length;

        // Validate the offset
        if (calculatedOffset < 0) {
            console.warn('SpanManager: Calculated negative offset, using 0');
            return 0;
        }

        if (calculatedOffset > originalText.length) {
            console.warn('SpanManager: Calculated offset beyond text length, using text length');
            return originalText.length;
        }

        console.log('SpanManager: Calculated offset:', calculatedOffset, 'for text length:', originalText.length);
        return calculatedOffset;
    }

    /**
     * Create a new span annotation
     */
    async createAnnotation(spanText, start, end, label) {
        console.log('SpanManager: Creating annotation:', { spanText, start, end, label });

        if (!this.currentInstanceId) {
            console.error('SpanManager: No current instance ID');
            this.showStatus('No instance loaded', 'error');
            return Promise.reject(new Error('No instance loaded'));
        }

        if (!this.currentSchema) {
            console.error('SpanManager: No current schema');
            this.showStatus('No schema selected', 'error');
            return Promise.reject(new Error('No schema selected'));
        }

        try {
            // Initialize annotations if not already done
            if (!this.annotations) {
                this.annotations = { spans: [] };
            }

            // Get existing spans to include in the request
            const existingSpans = this.getSpans();
            console.log('SpanManager: Existing spans before creating new one:', existingSpans);

            // Create the new span
            const newSpan = {
                name: label,
                start: start,
                end: end,
                title: label,
                value: spanText
            };

            // Combine existing spans with the new span
            const allSpans = [...existingSpans.map(span => ({
                name: span.label,
                start: span.start,
                end: span.end,
                title: span.label,
                value: span.text || span.value
            })), newSpan];

            console.log('SpanManager: Sending POST to /updateinstance with all spans:', allSpans);

            // OPTIMISTIC UPDATE: Add the new span to local state immediately
            // This ensures the visual overlay appears right away
            const optimisticSpan = {
                id: `temp_${Date.now()}`, // Temporary ID until server assigns one
                label: label, // This should be the actual label text (e.g., "happy", "sad", "angry")
                start: start,
                end: end,
                text: spanText,
                schema: this.currentSchema
            };

            this.annotations.spans.push(optimisticSpan);
            console.log('SpanManager: Added optimistic span to local state:', optimisticSpan);

            // Render spans immediately with the optimistic update
            this.renderSpans();
            console.log('SpanManager: Rendered spans with optimistic update');

            // Now make the API call
            const response = await fetch('/updateinstance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'span',
                    schema: this.currentSchema, // Use tracked schema
                    state: allSpans,
                    instance_id: this.currentInstanceId
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('SpanManager: POST successful, result:', result);

                this.showStatus(`Created ${label} annotation: "${spanText}"`, 'success');
                console.log('SpanManager: Annotation created:', result);
                return result; // Return the result
            } else {
                const error = await response.json();
                const errorMessage = `Error: ${error.error || 'Failed to create annotation'}`;

                // Remove the optimistic span since the API call failed
                this.annotations.spans = this.annotations.spans.filter(span => span.id !== optimisticSpan.id);
                this.renderSpans();

                this.showStatus(errorMessage, 'error');
                return Promise.reject(new Error(errorMessage));
            }
        } catch (error) {
            console.error('SpanManager: Error creating annotation:', error);

            // Remove the optimistic span since there was an error
            if (this.annotations && this.annotations.spans) {
                this.annotations.spans = this.annotations.spans.filter(span => span.id !== `temp_${Date.now()}`);
                this.renderSpans();
            }

            this.showStatus('Error creating annotation', 'error');
            return Promise.reject(error);
        }
    }

    /**
     * Delete a span annotation
     */
    async deleteSpan(annotationId) {
        console.log(`🔍 [DEBUG] SpanManager.deleteSpan() called for annotationId: ${annotationId}`);

        if (!this.currentInstanceId) {
            this.showStatus('No instance loaded', 'error');
            return;
        }

        if (!this.currentSchema) {
            this.showStatus('No schema selected', 'error');
            return;
        }

        try {
            // DEBUG: Track overlays before deletion
            const spanOverlays = document.getElementById('span-overlays');
            const overlaysBeforeDelete = spanOverlays ? spanOverlays.children.length : 0;
            console.log(`🔍 [DEBUG] SpanManager.deleteSpan() - Before deletion: ${overlaysBeforeDelete} overlays`);

            // Find the span to delete from current annotations
            const spanToDelete = this.annotations.spans.find(span => span.id === annotationId);
            if (!spanToDelete) {
                this.showStatus('Span not found', 'error');
                return;
            }

            console.log('SpanManager: Deleting span:', spanToDelete);

            // Send deletion request with value: null to indicate deletion
            const response = await fetch('/updateinstance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'span',
                    schema: this.currentSchema,
                    state: [
                        {
                            name: spanToDelete.label,
                            start: spanToDelete.start,
                            end: spanToDelete.end,
                            title: spanToDelete.label,
                            value: null  // This signals deletion
                        }
                    ],
                    instance_id: this.currentInstanceId
                })
            });

            if (response.ok) {
                console.log('🔍 [DEBUG] SpanManager.deleteSpan() - Backend deletion successful, reloading annotations');
                // Reload all annotations to ensure consistency
                await this.loadAnnotations(this.currentInstanceId);
                this.showStatus('Annotation deleted', 'success');
                console.log('SpanManager: Annotation deleted:', annotationId);

                // DEBUG: Track overlays after deletion and reload
                const overlaysAfterDelete = spanOverlays ? spanOverlays.children.length : 0;
                console.log(`🔍 [DEBUG] SpanManager.deleteSpan() - After deletion and reload: ${overlaysAfterDelete} overlays`);

                // --- FIX: If no spans remain, force overlays to be cleared ---
                if (this.getSpans().length === 0 && spanOverlays) {
                    spanOverlays.innerHTML = '';
                    console.log('🔍 [FIX] No spans remain after deletion, overlays forcibly cleared.');
                }
            } else {
                const error = await response.json();
                this.showStatus(`Error: ${error.error || 'Failed to delete annotation'}`, 'error');
            }
        } catch (error) {
            console.error('SpanManager: Error deleting annotation:', error);
            this.showStatus('Error deleting annotation', 'error');
        }
    }

    /**
     * Show status message
     * DISABLED: Status messages are suppressed but code is preserved for future diagnostics
     */
    showStatus(message, type) {
        // Status messages are disabled - uncomment the code below to re-enable
        /*
        const statusDiv = document.getElementById('status');
        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';

            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
        */

        // Keep console logging for debugging (can be disabled if needed)
        console.log(`SpanManager: ${type.toUpperCase()} - ${message}`);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Get current annotations
     */
    getAnnotations() {
        return this.annotations;
    }

    /**
     * Get spans in a format suitable for testing and API consistency
     */
    getSpans() {
        console.log('🔍 [DEBUG] getSpans() called');
        console.log('🔍 [DEBUG] getSpans() - this.annotations:', this.annotations);
        console.log('🔍 [DEBUG] getSpans() - this.annotations?.spans:', this.annotations?.spans);

        if (!this.annotations || !this.annotations.spans) {
            console.log('🔍 [DEBUG] getSpans() - returning empty array (no annotations or spans)');
            return [];
        }

        console.log('🔍 [DEBUG] getSpans() - returning spans:', this.annotations.spans);
        return this.annotations.spans;
    }

    /**
     * Clear all annotations (for testing)
     */
    clearAnnotations() {
        this.annotations = {spans: []};
        this.renderSpans();
    }

    /**
     * Get the background color for a given label
     */
    getSpanColor(label) {
        // The colors structure is nested: {schema: {label: color}}
        // We need to search through all schemas to find the label
        if (this.colors) {
            for (const schema in this.colors) {
                if (this.colors[schema] && this.colors[schema][label]) {
                    const color = this.colors[schema][label];
                    // Add 40% opacity (66 in hex) to match backend rendering
                    return color + '66';
                }
            }
        }
        // Fallback color if label not found in colors
        return '#f0f0f066'; // A neutral gray with 40% opacity
    }

    /**
     * Calculate overlap depths and adjust span positioning for better visibility
     */
    calculateOverlapDepths(spans) {
        if (!spans || spans.length === 0) return [];

        // Sort spans by start position
        const sortedSpans = [...spans].sort((a, b) => a.start - b.start);
        const overlapMap = new Map();

        // Calculate overlaps and containment relationships
        for (let i = 0; i < sortedSpans.length; i++) {
            const currentSpan = sortedSpans[i];
            const currentKey = `${currentSpan.start}-${currentSpan.end}`;

            if (!overlapMap.has(currentKey)) {
                overlapMap.set(currentKey, {
                    span: currentSpan,
                    overlaps: [],
                    containedBy: [],
                    contains: [],
                    depth: 0,
                    heightMultiplier: 1.0
                });
            }

            // Check for overlaps with other spans
            for (let j = i + 1; j < sortedSpans.length; j++) {
                const otherSpan = sortedSpans[j];

                // Check if spans overlap
                if (this.spansOverlap(currentSpan, otherSpan)) {
                    const otherKey = `${otherSpan.start}-${otherSpan.end}`;

                    // Add to current span's overlaps
                    overlapMap.get(currentKey).overlaps.push(otherSpan);

                    // Add to other span's overlaps
                    if (!overlapMap.has(otherKey)) {
                        overlapMap.set(otherKey, {
                            span: otherSpan,
                            overlaps: [],
                            containedBy: [],
                            contains: [],
                            depth: 0,
                            heightMultiplier: 1.0
                        });
                    }
                    overlapMap.get(otherKey).overlaps.push(currentSpan);

                    // Check for containment relationships
                    if (this.spansContain(currentSpan, otherSpan)) {
                        // currentSpan completely contains otherSpan
                        overlapMap.get(currentKey).contains.push(otherSpan);
                        overlapMap.get(otherKey).containedBy.push(currentSpan);
                    } else if (this.spansContain(otherSpan, currentSpan)) {
                        // otherSpan completely contains currentSpan
                        overlapMap.get(otherKey).contains.push(currentSpan);
                        overlapMap.get(currentKey).containedBy.push(currentSpan);
                    }
                }
            }
        }

        // Calculate depths using a simpler approach to avoid recursion issues
        let changed = true;
        let maxIterations = 100; // Prevent infinite loops
        let iteration = 0;

        while (changed && iteration < maxIterations) {
            changed = false;
            iteration++;

            for (const [spanKey, spanData] of overlapMap) {
                let maxOverlapDepth = 0;

                // Find the maximum depth of overlapping spans
                for (const overlappingSpan of spanData.overlaps) {
                    const overlappingKey = `${overlappingSpan.start}-${overlappingSpan.end}`;
                    const overlappingData = overlapMap.get(overlappingKey);
                    if (overlappingData) {
                        maxOverlapDepth = Math.max(maxOverlapDepth, overlappingData.depth);
                    }
                }

                // Set this span's depth to one more than the maximum overlap depth
                const newDepth = maxOverlapDepth + 1;
                if (newDepth !== spanData.depth) {
                    spanData.depth = newDepth;
                    changed = true;
                }
            }
        }

        if (iteration >= maxIterations) {
            console.warn('SpanManager: Max iterations reached in overlap depth calculation');
        }

        // Calculate height multipliers for visual distinction
        this.calculateHeightMultipliers(overlapMap);

        const result = Array.from(overlapMap.values());
        return result;
    }

    /**
     * Check if two spans overlap
     */
    spansOverlap(span1, span2) {
        return span1.start < span2.end && span2.start < span1.end;
    }

    /**
     * Check if span1 completely contains span2
     */
    spansContain(span1, span2) {
        return span1.start <= span2.start && span1.end >= span2.end;
    }

    /**
     * Calculate height multipliers for overlays based on overlap relationships
     */
    calculateHeightMultipliers(overlapMap) {
        // Base height for all overlays
        const baseHeight = 1.0;
        const heightIncrement = 0.3; // Additional height per level
        const maxHeightMultiplier = 3.0; // Cap the maximum height

        // First pass: calculate height for containing spans
        for (const [spanKey, spanData] of overlapMap) {
            if (spanData.contains.length > 0) {
                // This span contains other spans - make it taller
                const containmentLevel = this.getContainmentLevel(spanData, overlapMap);
                spanData.heightMultiplier = Math.min(
                    baseHeight + (containmentLevel * heightIncrement),
                    maxHeightMultiplier
                );
            }
        }

        // Second pass: adjust heights for partially overlapping spans
        for (const [spanKey, spanData] of overlapMap) {
            if (spanData.overlaps.length > 0 && spanData.contains.length === 0) {
                // This span overlaps but doesn't contain others - make it slightly taller
                const overlapLevel = this.getOverlapLevel(spanData, overlapMap);
                const currentHeight = spanData.heightMultiplier;
                const newHeight = Math.min(
                    currentHeight + (overlapLevel * heightIncrement * 0.5),
                    maxHeightMultiplier
                );
                spanData.heightMultiplier = newHeight;
            }
        }
    }

    /**
     * Get the containment level (how many levels of containment this span has)
     */
    getContainmentLevel(spanData, overlapMap) {
        let maxLevel = 0;
        const visited = new Set();

        const traverseContainment = (span, level) => {
            if (visited.has(`${span.start}-${span.end}`)) return;
            visited.add(`${span.start}-${span.end}`);

            maxLevel = Math.max(maxLevel, level);

            for (const containedSpan of spanData.contains) {
                const containedKey = `${containedSpan.start}-${containedSpan.end}`;
                const containedData = overlapMap.get(containedKey);
                if (containedData && containedData.contains.length > 0) {
                    traverseContainment(containedSpan, level + 1);
                }
            }
        };

        traverseContainment(spanData.span, 1);
        return maxLevel;
    }

    /**
     * Get the overlap level (how many spans this overlaps with)
     */
    getOverlapLevel(spanData, overlapMap) {
        return spanData.overlaps.length;
    }

    /**
     * Apply overlap-based styling to span elements
     */
    applyOverlapStyling(spanElements, overlapData) {
        // Only apply overlap styling if there are actual overlaps
        const spansWithOverlaps = overlapData.filter(d => d.overlaps.length > 0);

        if (spansWithOverlaps.length === 0) {
            // Remove all overlap styling from all spans
            spanElements.forEach(spanElement => {
                spanElement.classList.remove('span-overlap');
                spanElement.classList.forEach(className => {
                    if (className.startsWith('overlap-depth-')) {
                        spanElement.classList.remove(className);
                    }
                });
                spanElement.style.removeProperty('--overlap-height');
                spanElement.style.removeProperty('--overlap-offset');
                spanElement.style.removeProperty('--overlap-depth');
                spanElement.style.removeProperty('--max-depth');
                spanElement.style.removeProperty('z-index');
            });
            return;
        }

        const maxDepth = Math.max(...overlapData.map(d => d.depth), 0);

        spanElements.forEach(spanElement => {
            const start = parseInt(spanElement.dataset.start);
            const end = parseInt(spanElement.dataset.end);
            const spanKey = `${start}-${end}`;

            const data = overlapData.find(d =>
                d.span.start === start && d.span.end === end
            );

            // Only apply overlap styling if the span actually has overlaps
            if (data && data.overlaps.length > 0) {
                // Invert the depth so outermost is at base, innermost is on top
                const layer = maxDepth - data.depth + 1;
                const baseHeight = 1.2; // Base line height
                const heightIncrement = 0.3; // Additional height per layer
                const offsetIncrement = 0.2; // Vertical offset per layer

                const height = baseHeight + (layer * heightIncrement);
                const offset = (layer - 1) * offsetIncrement;

                // Apply CSS custom properties for dynamic styling
                spanElement.style.setProperty('--overlap-height', `${height}em`);
                spanElement.style.setProperty('--overlap-offset', `${offset}em`);
                spanElement.style.setProperty('--overlap-depth', layer);
                spanElement.style.setProperty('--max-depth', maxDepth);

                // Add overlap class for CSS targeting
                spanElement.classList.add('span-overlap');
                spanElement.classList.add(`overlap-depth-${layer}`);

                // Add z-index to ensure proper layering (innermost on top)
                spanElement.style.zIndex = layer;
            } else {
                // Remove any existing overlap styling for non-overlapping spans
                spanElement.classList.remove('span-overlap');
                spanElement.classList.forEach(className => {
                    if (className.startsWith('overlap-depth-')) {
                        spanElement.classList.remove(className);
                    }
                });
                spanElement.style.removeProperty('--overlap-height');
                spanElement.style.removeProperty('--overlap-offset');
                spanElement.style.removeProperty('--overlap-depth');
                spanElement.style.removeProperty('--max-depth');
                spanElement.style.removeProperty('z-index');
            }
        });
    }

    /**
     * Aggressively clear all overlays and internal state with deep logging
     */
    clearAllStateAndOverlays() {
        console.log('[DEEP DEBUG] clearAllStateAndOverlays called');
        this.debugState.clearAllStateCalls++;

        // Log state before clearing
        this.logDebugState('clearAllStateAndOverlays_before', {
            overlayCount: this.getCurrentOverlayCount(),
            annotationsCount: this.annotations?.spans?.length || 0
        });

        // Clear overlays
        const spanOverlays = document.getElementById('span-overlays');
        if (spanOverlays) {
            const beforeCount = spanOverlays.children.length;
            console.log('[DEEP DEBUG] Clearing overlays, count before:', beforeCount);

            while (spanOverlays.firstChild) {
                spanOverlays.removeChild(spanOverlays.firstChild);
            }

            // Force reflow
            spanOverlays.offsetHeight;

            // Double-check
            const remaining = spanOverlays.querySelectorAll('.span-overlay');
            if (remaining.length > 0) {
                console.warn('[DEEP DEBUG] Overlays still present after clear, forcing removal');
                remaining.forEach(node => {
                    if (node.parentNode) {
                        node.parentNode.removeChild(node);
                    }
                });
            }

            const afterCount = spanOverlays.children.length;
            console.log('[DEEP DEBUG] Overlays cleared, count after:', afterCount);
        }

        // Reset internal state
        // Don't clear annotations if they were just loaded from API
        // this.annotations = {spans: []};
        // Don't clear currentSchema - it should persist across state clearing
        // this.currentSchema = null;
        this.selectedLabel = null;
        // Don't reset isInitialized - it should persist across state clearing
        // this.isInitialized = false;

        this.logDebugState('clearAllStateAndOverlays_after', {
            overlayCount: this.getCurrentOverlayCount(),
            annotationsCount: this.annotations?.spans?.length || 0
        });

        console.log('[DEEP DEBUG] Internal state reset complete');
    }

    /**
     * Get current overlay count for debugging
     */
    getCurrentOverlayCount() {
        const spanOverlays = document.getElementById('span-overlays');
        return spanOverlays ? spanOverlays.children.length : 0;
    }

    /**
     * Update internal state from API data for correct positioning
     * This method uses the API response which has the correct original positions
     * instead of trying to calculate positions from the DOM
     */
    updateInternalStateFromAPI() {
        console.log('SpanManager: Updating internal state from API data');

        // Use the API response data that was already fetched in loadAnnotations
        if (this.annotations && this.annotations.spans) {
            console.log('SpanManager: Using existing API data for internal state');
            console.log('SpanManager: Internal state updated from API, spans count:', this.annotations.spans.length);
            return;
        }

        console.warn('SpanManager: No API data available for internal state update');
    }

    /**
     * Update internal state from server-rendered spans in the DOM
     * This method extracts span information from existing DOM elements
     * instead of clearing and re-rendering them
     */
    updateInternalStateFromDOM() {
        console.log('SpanManager: Updating internal state from DOM');

        const textContent = document.getElementById('text-content');
        if (!textContent) {
            console.warn('SpanManager: text-content element not found for DOM state update');
            return;
        }

        const existingSpans = textContent.querySelectorAll('.span-highlight');
        console.log('SpanManager: Found', existingSpans.length, 'server-rendered spans in DOM');

        // Convert DOM spans to internal annotation format
        const spans = [];
        for (const spanElement of existingSpans) {
            const spanData = {
                id: spanElement.getAttribute('data-annotation-id'),
                label: spanElement.getAttribute('data-label'),
                schema: spanElement.getAttribute('schema'),
                start: this.getSpanStartPositionFromDOM(spanElement),
                end: this.getSpanEndPositionFromDOM(spanElement),
                text: spanElement.textContent
            };

            console.log('SpanManager: Extracted span from DOM:', spanData);
            spans.push(spanData);
        }

        // Update internal state to match DOM
        this.annotations = { spans: spans };

        // Set schema from first span if available
        if (spans.length > 0 && spans[0].schema && !this.currentSchema) {
            this.currentSchema = spans[0].schema;
            console.log('SpanManager: Set schema from DOM spans:', this.currentSchema);
        }

        console.log('SpanManager: Internal state updated from DOM, spans count:', spans.length);
    }

    /**
     * Get the start position of a span element from the DOM
     * This method calculates position based on the current DOM structure
     */
    getSpanStartPositionFromDOM(spanElement) {
        const textContent = document.getElementById('text-content');
        if (!textContent) return 0;

        // Get all text nodes and elements in order
        const walker = document.createTreeWalker(
            textContent,
            NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
            null,
            false
        );

        let currentPos = 0;
        let node;

        while (node = walker.nextNode()) {
            if (node === spanElement) {
                // Found the span element, return current position
                return currentPos;
            } else if (node.nodeType === Node.TEXT_NODE) {
                // Text node, add its length to current position
                currentPos += node.textContent.length;
            } else if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains('span-highlight')) {
                // This is a span element (but not the one we're looking for)
                // Add the text content length to current position
                currentPos += node.textContent.length;
            }
            // Skip other elements (they don't contribute to text position)
        }

        console.warn('SpanManager: Could not find span element in DOM walker');
        return 0;
    }

    /**
     * Get the end position of a span element from the DOM
     */
    getSpanEndPositionFromDOM(spanElement) {
        const startPos = this.getSpanStartPositionFromDOM(spanElement);
        const spanText = spanElement.textContent;
        return startPos + spanText.length;
    }

    /**
     * Enhanced onInstanceChange with deep logging
     */
    onInstanceChange(newInstanceId) {
        console.log('🔍 [NAVIGATION] Instance change detected:', {
            oldInstanceId: this.currentInstanceId,
            newInstanceId: newInstanceId
        });

        // Check for text duplication before navigation
        const textContent = document.getElementById('text-content');
        if (textContent) {
            const currentText = textContent.textContent || '';
            const originalText = textContent.getAttribute('data-original-text') || '';
            console.log('🔍 [NAVIGATION] Text content before navigation:', {
                currentText: currentText.substring(0, 100) + '...',
                originalText: originalText.substring(0, 100) + '...',
                hasDuplication: currentText.includes(originalText + originalText),
                textContentHTML: textContent.innerHTML.substring(0, 200) + '...'
            });
        }

        this.currentInstanceId = newInstanceId;

        // Clear existing state
        this.clearAllStateAndOverlays();

        // Load annotations for the new instance
        this.loadAnnotations(newInstanceId);
    }

    /**
     * Clear text selection properly
     */
    clearTextSelection() {
        console.log('🔍 [UNIFIED] Clearing text selection');

        // Clear selection using multiple methods for maximum compatibility
        if (window.getSelection) {
            const selection = window.getSelection();
            if (selection) {
                selection.removeAllRanges();
            }
        }

        // Also clear selection using document methods
        if (document.selection) {
            document.selection.empty();
        }

        // Clear any active text selection in the text element
        const textElement = document.getElementById('instance-text');
        if (textElement) {
            // Remove any selection styling
            textElement.style.userSelect = 'text';
            textElement.style.webkitUserSelect = 'text';
            textElement.style.mozUserSelect = 'text';
            textElement.style.msUserSelect = 'text';
        }

        console.log('🔍 [UNIFIED] Text selection cleared');
    }

    /**
     * Reinitialize positioning strategy for new instance
     */
    async reinitializePositioningStrategy() {
        console.log('[DEEP DEBUG] Reinitializing positioning strategy');

        const textContent = document.getElementById('text-content');
        if (textContent) {
            this.positioningStrategy = new UnifiedPositioningStrategy(textContent);
            await this.positioningStrategy.initialize();
            console.log('[DEEP DEBUG] Positioning strategy reinitialized successfully');
        } else {
            console.error('[DEEP DEBUG] Text content element not found during reinitialization');
        }
    }

    /**
     * Remove all span overlays from the DOM and reset internal state
     */
    clearAllSpanOverlays() {
        const spanOverlays = document.getElementById('span-overlays');
        if (spanOverlays) {
            while (spanOverlays.firstChild) {
                spanOverlays.removeChild(spanOverlays.firstChild);
            }
        }
        this.annotations = {spans: []};
        console.log('[DEFENSIVE] Cleared all span overlays and reset annotations');
    }

    detectTextDuplication() {
        const textContent = document.getElementById('text-content');
        if (!textContent) {
            console.log('🔍 [DUPLICATION] text-content element not found');
            return;
        }

        const currentText = textContent.textContent || '';
        const originalText = textContent.getAttribute('data-original-text') || '';
        const innerHTML = textContent.innerHTML;

        console.log('🔍 [DUPLICATION] Text duplication check:', {
            currentTextLength: currentText.length,
            originalTextLength: originalText.length,
            hasHTMLMarkup: innerHTML.includes('<') && innerHTML.includes('>'),
            htmlMarkup: innerHTML.includes('<') ? innerHTML.match(/<[^>]*>/g)?.slice(0, 3) : null,
            hasDuplication: currentText.includes(originalText + originalText),
            currentTextSample: currentText.substring(0, 100) + '...',
            originalTextSample: originalText.substring(0, 100) + '...'
        });

        // Check for specific issues mentioned
        if (innerHTML.includes('style="position: relative; z-index: 1; pointer-events: auto;">')) {
            console.warn('🔍 [DUPLICATION] Found problematic markup in innerHTML');
        }

        if (currentText.includes(originalText + originalText)) {
            console.error('🔍 [DUPLICATION] TEXT DUPLICATION DETECTED!');
        }
    }

    cleanupDataOriginalText() {
        const textContent = document.getElementById('text-content');
        if (!textContent) {
            console.log('🔍 [CLEANUP] text-content element not found');
            return;
        }

        const currentDataOriginalText = textContent.getAttribute('data-original-text');
        if (currentDataOriginalText) {
            // Check if it contains HTML markup
            if (currentDataOriginalText.includes('<') && currentDataOriginalText.includes('>')) {
                console.warn('🔍 [CLEANUP] Found HTML markup in data-original-text, cleaning it');
                const cleanText = currentDataOriginalText.replace(/<[^>]*>/g, '').trim();
                textContent.setAttribute('data-original-text', cleanText);
                console.log('🔍 [CLEANUP] Cleaned data-original-text:', cleanText);
            }
        }

        // Also check if the textContent itself has HTML markup
        const innerHTML = textContent.innerHTML;
        if (innerHTML.includes('<') && innerHTML.includes('>')) {
            console.warn('🔍 [CLEANUP] Found HTML markup in textContent.innerHTML');
            // Get the plain text content
            const plainText = textContent.textContent || textContent.innerText || '';
            console.log('🔍 [CLEANUP] Plain text from textContent:', plainText);

            // Set the plain text as data-original-text if it's not already set
            if (!textContent.hasAttribute('data-original-text')) {
                textContent.setAttribute('data-original-text', plainText);
                console.log('🔍 [CLEANUP] Set data-original-text to plain text');
            }
        }
    }
}

/**
 * Unified text positioning utilities for span annotations
 * These functions ensure consistent positioning between frontend and backend
 */

/**
 * Get the original text content for positioning calculations
 * This ensures we always work with the clean text without HTML markup
 */
function getOriginalTextForPositioning(container) {
    // First try to get the original text from data attribute
    if (container.hasAttribute('data-original-text')) {
        return container.getAttribute('data-original-text');
    }

    // Fallback to textContent (stripped of HTML)
    return container.textContent || container.innerText || '';
}

/**
 * Calculate text offsets from a DOM selection range
 * This is the primary function for converting user selections to backend-compatible offsets
 */
function calculateTextOffsetsFromSelection(container, range) {
    console.log('🔍 [DEBUG] calculateTextOffsetsFromSelection - ENTRY POINT');

    // Get the original text for positioning
    const originalText = getOriginalTextForPositioning(container);
    console.log('🔍 [DEBUG] calculateTextOffsetsFromSelection - originalText length:', originalText.length);

    // Get the selected text
    const selectedText = range.toString().trim();
    console.log('🔍 [DEBUG] calculateTextOffsetsFromSelection - selectedText:', selectedText);

    if (!selectedText) {
        console.warn('🔍 [DEBUG] calculateTextOffsetsFromSelection - No selected text');
        return { start: 0, end: 0 };
    }

    // Find the selection in the original text
    const startIndex = originalText.indexOf(selectedText);
    if (startIndex === -1) {
        console.warn('🔍 [DEBUG] calculateTextOffsetsFromSelection - Selected text not found in original text');
        return { start: 0, end: 0 };
    }

    const endIndex = startIndex + selectedText.length;

    console.log('🔍 [DEBUG] calculateTextOffsetsFromSelection - calculated offsets:', {
        start: startIndex,
        end: endIndex,
        selectedText: selectedText,
        extractedText: originalText.substring(startIndex, endIndex)
    });

    return { start: startIndex, end: endIndex };
}

/**
 * Get bounding rectangles for a text range using original text offsets
 * This function positions overlays based on the actual rendered text positions
 */
function getCharRangeBoundingRect(container, start, end) {
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - ENTRY POINT');
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - start:', start, 'end:', end);

    // Get the original text for verification
    const originalText = getOriginalTextForPositioning(container);
    const targetText = originalText.substring(start, end);
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - targetText:', targetText);

    // Get the actual rendered text content
    const renderedText = container.textContent || container.innerText || '';
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - renderedText length:', renderedText.length);
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - renderedText:', renderedText);

    // Find the target text in the rendered text
    const targetStart = renderedText.indexOf(targetText);
    if (targetStart === -1) {
        console.warn('🔍 [DEBUG] getCharRangeBoundingRect - Target text not found in rendered text');
        console.warn('🔍 [DEBUG] getCharRangeBoundingRect - Target text:', targetText);
        console.warn('🔍 [DEBUG] getCharRangeBoundingRect - Rendered text:', renderedText);
        return null;
    }

    const targetEnd = targetStart + targetText.length;
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - targetStart:', targetStart, 'targetEnd:', targetEnd);

    // Ensure the container has a text node for positioning
    let textNode = container.firstChild;
    if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
        console.warn('🔍 [DEBUG] getCharRangeBoundingRect - No text node found, using container');
        textNode = container;
    }

    // Create a range for the actual rendered text positions
    const range = document.createRange();
    range.setStart(textNode, targetStart);
    range.setEnd(textNode, targetEnd);

    // Get the bounding rectangles
    const rects = range.getClientRects();
    console.log('🔍 [DEBUG] getCharRangeBoundingRect - rects count:', rects.length);

    if (rects.length === 0) {
        console.warn('🔍 [DEBUG] getCharRangeBoundingRect - No bounding rects returned');
        return null;
    }

    return Array.from(rects);
}

/**
 * Legacy function - kept for compatibility but now delegates to the unified approach
 */
function getCharRangeBoundingRectFromTextNode(container, start, end) {
    return getCharRangeBoundingRect(container, start, end);
}

/**
 * Legacy function - kept for compatibility but now delegates to the unified approach
 */
function getCharRangeBoundingRectFromOriginalText(container, start, end) {
    return getCharRangeBoundingRect(container, start, end);
}

// CommonJS export for Jest
if (typeof module !== 'undefined' && module.exports) {
    module.exports.getCharRangeBoundingRect = getCharRangeBoundingRect;
}

// Initialize global span manager
window.spanManager = new SpanManager();
console.log('🔍 [DEBUG] typeof window.spanManager.handleTextSelection:', typeof window.spanManager.handleTextSelection);
console.log('🔍 [DEBUG] window.spanManager.handleTextSelection.toString:', window.spanManager.handleTextSelection && window.spanManager.handleTextSelection.toString());

// Debug: Check if spanManager is available
console.log('🔍 [DEBUG] spanManager created:', {
    spanManagerExists: !!window.spanManager,
    spanManagerType: window.spanManager ? window.spanManager.constructor.name : 'none',
    handleTextSelectionExists: window.spanManager ? typeof window.spanManager.handleTextSelection : 'none',
    handleTextSelectionType: window.spanManager ? window.spanManager.handleTextSelection.constructor.name : 'none'
});

// Robust initialization function
function initializeSpanManager() {
    console.log('[DEEP DEBUG] initializeSpanManager called');
    if (window.spanManager && !window.spanManager.isInitialized) {
        console.log('[DEEP DEBUG] Initializing span manager...');
        window.spanManager.initialize().then(() => {
            console.log('[DEEP DEBUG] Span manager initialization completed successfully');
        }).catch((error) => {
            console.error('[DEEP DEBUG] Span manager initialization failed:', error);
        });
    } else if (window.spanManager && window.spanManager.isInitialized) {
        console.log('[DEEP DEBUG] Span manager already initialized');
    } else {
        console.error('[DEEP DEBUG] Span manager not available for initialization');
    }
}

// Try to initialize immediately if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[DEEP DEBUG] DOMContentLoaded - Initializing span manager');
        initializeSpanManager();
    });
} else {
    console.log('[DEEP DEBUG] DOM already loaded - Initializing span manager immediately');
    initializeSpanManager();
}

// Additional initialization on window load to ensure everything is ready
window.addEventListener('load', () => {
    console.log('[DEEP DEBUG] Window load - Ensuring span manager is properly initialized');
    initializeSpanManager();
});

// Fallback initialization with retry mechanism
setTimeout(() => {
    if (window.spanManager && !window.spanManager.isInitialized) {
        console.log('[DEEP DEBUG] Fallback initialization - Span manager not initialized after timeout');
        initializeSpanManager();
    }
}, 1000);

/**
 * ===================== DEBUGGING & MAINTENANCE NOTES =====================
 * - All major state changes are logged with [DEBUG] or [DEFENSIVE] tags.
 * - If overlays persist across navigation, check onInstanceChange and clearAllSpanOverlays.
 * - If overlays are missing, check loadAnnotations and renderSpans logic.
 * - For browser-specific issues (esp. Firefox), see FIREFOX FIX comments.
 * - Selenium tests in tests/selenium/ can be used to automate bug reproduction.
 * ========================================================================
 */

/**
 * ===================== PURE CSS OVERLAY SYSTEM =====================
 * This section implements true CSS overlays without DOM manipulation
 * ===================================================================
 */

/**
 * Get font metrics for accurate character positioning
 * @param {HTMLElement} container - The text container element
 * @returns {Object} Font metrics including character width, line height, etc.
 */
function getFontMetrics(container) {
    const computedStyle = window.getComputedStyle(container);
    const fontSize = parseFloat(computedStyle.fontSize);
    const fontFamily = computedStyle.fontFamily;
    const lineHeight = parseFloat(computedStyle.lineHeight) || fontSize * 1.2;

    // Create a temporary canvas to measure character width
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.font = `${fontSize}px ${fontFamily}`;

    // Measure common characters to get average width
    const testChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ';
    const charWidths = {};

    for (let char of testChars) {
        charWidths[char] = ctx.measureText(char).width;
    }

    // Calculate average character width
    const totalWidth = Object.values(charWidths).reduce((sum, width) => sum + width, 0);
    const averageCharWidth = totalWidth / Object.keys(charWidths).length;

    return {
        fontSize,
        fontFamily,
        lineHeight,
        averageCharWidth,
        charWidths,
        containerPadding: {
            top: parseFloat(computedStyle.paddingTop) || 0,
            left: parseFloat(computedStyle.paddingLeft) || 0,
            right: parseFloat(computedStyle.paddingRight) || 0,
            bottom: parseFloat(computedStyle.paddingBottom) || 0
        }
    };
}

/**
 * Measure the width of a specific text string
 * @param {string} text - The text to measure
 * @param {Object} fontMetrics - Font metrics from getFontMetrics()
 * @returns {number} The width of the text in pixels
 */
function measureText(text, fontMetrics) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.font = `${fontMetrics.fontSize}px ${fontMetrics.fontFamily}`;
    return ctx.measureText(text).width;
}

/**
 * Calculate character positions for a text range using pure offset calculations
 * @param {string} text - The full text content
 * @param {number} start - Start character offset
 * @param {number} end - End character offset
 * @param {Object} fontMetrics - Font metrics from getFontMetrics()
 * @param {HTMLElement} container - The text container element
 * @returns {Array} Array of position objects for each line segment
 */
function calculateCharacterPositions(text, start, end, fontMetrics, container) {
    console.log('🔍 [PURE CSS] calculateCharacterPositions called:', { text, start, end });

    if (start >= end || start < 0 || end > text.length) {
        console.warn('🔍 [PURE CSS] Invalid range:', { start, end, textLength: text.length });
        return [];
    }

    const targetText = text.substring(start, end);
    console.log('🔍 [PURE CSS] Target text:', targetText);

    // Get container dimensions
    const containerRect = container.getBoundingClientRect();
    const containerWidth = containerRect.width - fontMetrics.containerPadding.left - fontMetrics.containerPadding.right;

    // Calculate positions for each character in the target text
    const positions = [];
    let currentLine = 0;
    let currentX = fontMetrics.containerPadding.left;
    let currentY = fontMetrics.containerPadding.top + (currentLine * fontMetrics.lineHeight);

    // Calculate positions for all characters up to the start position
    for (let i = 0; i < start; i++) {
        const char = text[i];
        const charWidth = fontMetrics.charWidths[char] || fontMetrics.averageCharWidth;

        if (char === '\n') {
            currentLine++;
            currentX = fontMetrics.containerPadding.left;
            currentY = fontMetrics.containerPadding.top + (currentLine * fontMetrics.lineHeight);
        } else {
            currentX += charWidth;
            if (currentX >= containerWidth) {
                currentLine++;
                currentX = fontMetrics.containerPadding.left + charWidth;
                currentY = fontMetrics.containerPadding.top + (currentLine * fontMetrics.lineHeight);
            }
        }
    }

    // Now calculate positions for the target text
    let segmentStart = { x: currentX, y: currentY, line: currentLine };
    let lastCharX = currentX;
    let lastCharY = currentY;

    for (let i = start; i < end; i++) {
        const char = text[i];
        const charWidth = fontMetrics.charWidths[char] || fontMetrics.averageCharWidth;

        if (char === '\n') {
            // End current segment and start new line
            if (segmentStart.x !== lastCharX || segmentStart.y !== lastCharY) {
                positions.push({
                    x: segmentStart.x,
                    y: segmentStart.y,
                    width: lastCharX - segmentStart.x,
                    height: fontMetrics.lineHeight,
                    line: segmentStart.line
                });
            }

            currentLine++;
            currentX = fontMetrics.containerPadding.left;
            currentY = fontMetrics.containerPadding.top + (currentLine * fontMetrics.lineHeight);
            segmentStart = { x: currentX, y: currentY, line: currentLine };
            lastCharX = currentX;
            lastCharY = currentY;
        } else if (char === ' ') {
            // Handle spaces - they have width but don't create segments
            currentX += charWidth;
            lastCharX = currentX;
            lastCharY = currentY;
        } else {
            currentX += charWidth;
            if (currentX >= containerWidth) {
                // End current segment and wrap to next line
                if (segmentStart.x !== lastCharX || segmentStart.y !== lastCharY) {
                    positions.push({
                        x: segmentStart.x,
                        y: segmentStart.y,
                        width: lastCharX - segmentStart.x,
                        height: fontMetrics.lineHeight,
                        line: segmentStart.line
                    });
                }

                currentLine++;
                currentX = fontMetrics.containerPadding.left + charWidth;
                currentY = fontMetrics.containerPadding.top + (currentLine * fontMetrics.lineHeight);
                segmentStart = { x: fontMetrics.containerPadding.left, y: currentY, line: currentLine };
            }

            lastCharX = currentX;
            lastCharY = currentY;
        }
    }

    // Add final segment if it has content
    // For single characters, we need to ensure we create a position even if start and end are the same
    if (segmentStart.x !== lastCharX || segmentStart.y !== lastCharY || start === end - 1) {
        const width = Math.max(lastCharX - segmentStart.x, fontMetrics.averageCharWidth);
        positions.push({
            x: segmentStart.x,
            y: segmentStart.y,
            width: width,
            height: fontMetrics.lineHeight,
            line: segmentStart.line
        });
    }

    console.log('🔍 [PURE CSS] Calculated positions:', positions);
    return positions;
}

/**
 * Create a pure CSS overlay element positioned using calculated coordinates
 * @param {Object} span - The span annotation object
 * @param {Array} positions - Array of position objects from calculateCharacterPositions
 * @param {HTMLElement} container - The container element
 * @param {Object} fontMetrics - Font metrics
 * @returns {HTMLElement} The created overlay element
 */
function createPureCSSOverlay(span, positions, container, fontMetrics) {
    console.log('🔍 [PURE CSS] createPureCSSOverlay called:', { span, positions });

    if (!positions || positions.length === 0) {
        console.warn('🔍 [PURE CSS] No positions provided for overlay');
        return null;
    }

    const overlay = document.createElement('div');
    overlay.className = 'span-overlay-pure';
    overlay.dataset.annotationId = span.id;
    overlay.dataset.start = span.start;
    overlay.dataset.end = span.end;
    overlay.dataset.label = span.label;

    // Position the overlay using the first position (for single-line spans)
    const position = positions[0];
    overlay.style.position = 'absolute';
    overlay.style.left = `${position.x}px`;
    overlay.style.top = `${position.y}px`;
    overlay.style.width = `${position.width}px`;
    overlay.style.height = `${position.height}px`;

    // Use the label color if available, otherwise default
    const backgroundColor = span.color || 'rgba(255, 234, 167, 0.4)';
    overlay.style.backgroundColor = backgroundColor;
    overlay.style.border = `1px solid ${span.color ? span.color.replace('66', '') : 'rgba(255, 193, 7, 0.3)'}`;
    overlay.style.borderRadius = '4px';
    overlay.style.zIndex = '1000';
    overlay.style.pointerEvents = 'auto';

    // For multi-line spans, create additional overlay elements
    if (positions.length > 1) {
        console.log('🔍 [PURE CSS] Creating multi-line overlay with', positions.length, 'segments');

        // Create a wrapper for multi-line overlays
        const wrapper = document.createElement('div');
        wrapper.className = 'span-overlay-multi-line';
        wrapper.style.position = 'absolute';
        wrapper.style.left = '0';
        wrapper.style.top = '0';
        wrapper.style.width = '100%';
        wrapper.style.height = '100%';
        wrapper.style.pointerEvents = 'none';

        // Add individual segments
        positions.forEach((pos, index) => {
            const segment = document.createElement('div');
            segment.className = 'span-overlay-segment';
            segment.style.position = 'absolute';
            segment.style.left = `${pos.x}px`;
            segment.style.top = `${pos.y}px`;
            segment.style.width = `${pos.width}px`;
            segment.style.height = `${pos.height}px`;
            segment.style.backgroundColor = 'inherit';
            segment.style.borderRadius = '4px';
            wrapper.appendChild(segment);
        });

        overlay.appendChild(wrapper);
    }

    // Add label - positioned above the overlay
    const label = document.createElement('span');
    label.className = 'span-label';
    label.textContent = span.label;
    label.style.position = 'absolute';
    label.style.top = '-25px';
    label.style.left = '0';
    label.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    label.style.color = 'white';
    label.style.padding = '2px 6px';
    label.style.borderRadius = '3px';
    label.style.fontSize = '12px';
    label.style.pointerEvents = 'auto';
    label.style.zIndex = '1001';
    label.style.display = 'block';
    label.style.fontWeight = 'bold';
    label.style.whiteSpace = 'nowrap';
    overlay.appendChild(label);

    // Add delete button - positioned in top-right corner
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'span-delete-btn';
    deleteBtn.innerHTML = '×';
    deleteBtn.title = 'Delete span';
    deleteBtn.style.position = 'absolute';
    deleteBtn.style.top = '-8px';
    deleteBtn.style.right = '-8px';
    deleteBtn.style.backgroundColor = '#dc3545';
    deleteBtn.style.color = 'white';
    deleteBtn.style.border = 'none';
    deleteBtn.style.borderRadius = '50%';
    deleteBtn.style.width = '18px';
    deleteBtn.style.height = '18px';
    deleteBtn.style.fontSize = '14px';
    deleteBtn.style.cursor = 'pointer';
    deleteBtn.style.pointerEvents = 'auto';
    deleteBtn.style.zIndex = '1002';
    deleteBtn.style.display = 'flex';
    deleteBtn.style.alignItems = 'center';
    deleteBtn.style.justifyContent = 'center';
    deleteBtn.style.fontWeight = 'bold';
    deleteBtn.style.lineHeight = '1';
    deleteBtn.style.transition = 'all 0.2s ease';
    deleteBtn.onclick = (e) => {
        e.stopPropagation();
        if (window.spanManager) {
            window.spanManager.deleteSpan(span.id);
        }
    };
    overlay.appendChild(deleteBtn);

    console.log('🔍 [PURE CSS] Created overlay element:', overlay);
    return overlay;
}

/**
 * Pure CSS text selection offset calculation
 * @param {HTMLElement} container - The text container
 * @param {Range} range - The DOM range object
 * @returns {Object} Object with start and end offsets
 */
function calculateTextOffsetsPureCSS(container, range) {
    console.log('🔍 [PURE CSS] calculateTextOffsetsPureCSS called');

    const originalText = getOriginalTextForPositioning(container);
    const selectedText = range.toString().trim();

    if (!selectedText) {
        return { start: 0, end: 0 };
    }

    // Find the selection in the original text
    const startIndex = originalText.indexOf(selectedText);
    if (startIndex === -1) {
        console.warn('🔍 [PURE CSS] Selected text not found in original text');
        return { start: 0, end: 0 };
    }

    const endIndex = startIndex + selectedText.length;

    console.log('🔍 [PURE CSS] Calculated offsets:', { start: startIndex, end: endIndex });
    return { start: startIndex, end: endIndex };
}