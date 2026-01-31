export const name = "quillmodules";

import React from 'react';
import PropTypes from "prop-types";
import { BlotConstructor, type Blot } from 'parchment';
export { Blot };
import Quill, { Delta } from 'quill';
export { Quill, Delta };
import QuillNextEditor from "quill-next-react";
import { tableId } from "quill/dist/formats/table";
import deepmerge from 'deepmerge';
import Container from "quill/dist/blots/container";
import Block from "quill/dist/blots/block";
// import OriginalSoftBreak from "quill/dist/blots/soft-break";
// import Break from "quill/dist/blots/break";
import QuillImageDropAndPaste from 'quill-image-drop-and-paste';
import BlotFormatter from '@enzedonline/quill-blot-formatter2';
import htmlEditButton from "quill-html-edit-button";
import { Mention, MentionBlot } from 'quill-mention';
import { RegisterImportPool, type ImportPool, getExReady } from "./Base";

import "@enzedonline/quill-blot-formatter2/dist/css/quill-blot-formatter2.css"; // align styles
import "./quillmodules.css";

import * as constants from './constants';
import * as t from './types';

// ============= TextBox Blot and Formatter Module =============
//
// TextBox implementation provides bordered, resizable text containers with alignment support.
// 
// Architecture:
// - TextBoxBlot: Container blot that holds one or more TextBoxBlock children
// - TextBoxBlock: Block-level blot (paragraph) that lives inside a TextBoxBlot
// - TextBoxFormatter: UI module for resize handles and alignment toolbar
//
// Key features:
// 1. Side-by-side layout: Multiple textboxes with different IDs stay separate
//    - Implemented via checkMerge() preventing merging of textboxes with different IDs
// 2. Float-based alignment: Left/right alignments use CSS float for text wrapping
// 3. Automatic wrapping: TextBoxBlock automatically wraps itself in TextBoxBlot during optimize
// 4. Dynamic repositioning: Overlay adjusts when text changes or alignment is applied
//
// Delta format:
// - textbox-block: string (ID) - Block format identifying which textbox the block belongs to
// - textbox: {width, align, id} - Container format for full textbox configuration
// - For insertion: Only textbox-block is needed; TextBoxBlock.optimize() creates container
//
// Similar to Quill's table implementation but simpler (no rows/cells, just container+blocks)
//
// ============= End TextBox Documentation =============

// const Container = Quill.import('blots/container');
// const tableId = Quill.import('formats/table').tableId;
// const Block = Quill.import('blots/block');
// const OriginalSoftBreak = Quill.import('blots/soft-break');
// const Break = Quill.import('blots/break');
// const Parchment = Quill.import('parchment');

/**
 * Generate unique ID for textbox containers and their children
 * Similar to tableId() in table format
 */
export function textboxId() {
    const id = Math.random().toString(36).slice(2, 6);
    return `textbox-${id}`;
}

/**
 * TextBoxBreak - Custom Break blot for use inside TextBox
 * Extends Break with custom className for styling
 */
// class TextBoxBreak extends Break {
//     static blotName = 'textbox-break';
//     static className = 'ql-textbox-break';
// }

/**
 * TextBoxBlock - Custom BlockBlot for use inside TextBox container
 * Represents a paragraph or block of text within the text box.
 * 
 * Each block has a data-textbox-id attribute that links it to its parent container.
 * When not in a textbox, the optimize() method automatically wraps the block in a TextBoxBlot.
 * 
 * Format: textbox-block (string) - The ID of the textbox this block belongs to
 */
class TextBoxBlock extends Block {
    static blotName = 'textbox-block';
    static tagName = 'P';
    static className = 'ql-textbox-block';

    static create(value?: string): HTMLElement {
        constants.debugMessage('TextBoxBlock.create', value);
        const node = super.create(value) as HTMLElement;
        // Set data-textbox-id to track which textbox this block belongs to
        if (value) {
            node.setAttribute('data-textbox-id', value);
        } else {
            node.setAttribute('data-textbox-id', textboxId());
        }
        return node;
    }

    static formats(domNode: HTMLElement): string | undefined {
        if (domNode.hasAttribute('data-textbox-id')) {
            return domNode.getAttribute('data-textbox-id') || undefined;
        }
        return undefined;
    }

    getTextBoxId(): string | undefined {
        return (this.domNode as HTMLElement).getAttribute('data-textbox-id') || undefined;
    }

    format(name: string, value: unknown): void {
        if (name === TextBoxBlock.blotName && value) {
            (this.domNode as HTMLElement).setAttribute('data-textbox-id', String(value));
        } else {
            super.format(name, value);
        }
    }

    formats(): { [index: string]: unknown } {
        return { [this.statics.blotName]: TextBoxBlock.formats(this.domNode as HTMLElement) };
    }

    // Get the parent textbox container
    textbox() {
        return this.parent && this.parent.statics.blotName === 'textbox' ? this.parent : null;
    }

    /**
     * Optimize ensures this block is always wrapped in a TextBoxBlot container.
     * When a block is created outside a textbox (e.g., from Delta insertion),
     * this method automatically wraps it in a new TextBoxBlot.
     * 
     * The created textbox uses default values (50% width, no alignment) since
     * the full textbox format is typically specified separately in the Delta.
     */
    optimize(contextOrMutations: Record<string, unknown> | MutationRecord[]): void {
        // Handle both signatures: optimize(context) and optimize(mutations, context)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        super.optimize(contextOrMutations as any);
        
        // If not in a textbox, wrap in a new textbox container
        if (this.parent) {
            if (this.parent.statics.blotName !== 'textbox') {
                // The textbox format (with align/width/id) is stored as a line attribute
                // We need to check the cache or domNode attributes for this information
                const width = '50%';
                const align = '';

                const textbox = this.scroll.create('textbox', { width, align }) as TextBoxBlot;
                textbox.appendChild(this);
                this.replaceWith(textbox);
            }
        }
    }
}

/**
 * TextBoxSoftBreak - Custom SoftBreak blot for use inside TextBox
 * Tracks parent textbox via data-textbox-id attribute
 */
// class TextBoxSoftBreak extends OriginalSoftBreak {
//     static blotName = 'textbox-soft-break';
//     static className = 'ql-textbox-soft-break';

//     static create(value?: string): HTMLElement {
//         const node = super.create(value) as HTMLElement;
//         // Set data-textbox-id to track which textbox this soft break belongs to
//         if (value) {
//             node.setAttribute('data-textbox-id', value);
//         } else {
//             node.setAttribute('data-textbox-id', textboxId());
//         }
//         return node;
//     }

//     static formats(domNode: HTMLElement): string | undefined {
//         if (domNode.hasAttribute('data-textbox-id')) {
//             return domNode.getAttribute('data-textbox-id') || undefined;
//         }
//         return undefined;
//     }

//     format(name: string, value: unknown): void {
//         if (name === TextBoxSoftBreak.blotName && value) {
//             (this.domNode as HTMLElement).setAttribute('data-textbox-id', String(value));
//         }
//     }

//     // Get the parent textbox container
//     textbox() {
//         return this.parent && this.parent.statics.blotName === 'textbox' ? this.parent : null;
//     }
// }

type TextBoxBlotFormats = { width?: string; align?: string; id?: string };

/**
 * TextBox Container Blot - A bordered, resizable text container
 * Contains TextBoxBlock children and supports alignment and resizing.
 * 
 * Features:
 * - Resizable via drag handles (BlotFormatter integration)
 * - Alignment: left (float left), right (float right), center (block centered)
 * - Side-by-side layout: Multiple textboxes with different IDs stay separate
 * - Each textbox has a unique ID for tracking and preventing merges
 * 
 * Format: textbox (object) - { width: string, align: 'left'|'right'|'center'|'', id: string }
 * 
 * Implementation notes:
 * - checkMerge() prevents merging textboxes with different IDs
 * - optimize() ensures proper structure and ID synchronization
 * - Alignment uses CSS float for left/right, allowing text wrap
 */
class TextBoxBlot extends Container {
    static blotName = 'textbox';
    static tagName = 'DIV';
    static className = 'ql-textbox';
    static defaultChild = TextBoxBlock;
    // static allowedChildren = [TextBoxBlock, TextBoxSoftBreak, TextBoxBreak];
    static allowedChildren: BlotConstructor[] = [TextBoxBlock];
    
    get textboxId(): string {
        return this.children.head
            ? (this.children.head as TextBoxBlock | TextBoxTable).getTextBoxId() || ''
            : '';
    }

    static create(value?: TextBoxBlotFormats | string): HTMLElement {
        constants.debugMessage('TextBoxBlot.create', value);
        const node = super.create() as HTMLElement;

        // Parse value
        const config = typeof value === 'string' ? {} : (value || {});

        // Apply width
        if (config.width) {
            node.style.width = config.width;
            node.setAttribute('data-width', config.width);
        } else {
            node.style.width = '50%';
            node.setAttribute('data-width', '50%');
        }
        
        // Apply alignment
        if (config.align) {
            node.setAttribute('data-align', config.align);
            node.classList.add(`ql-textbox-align-${config.align}`);
        }
        
        return node;
    }

    static formats(domNode: HTMLElement): TextBoxBlotFormats {
        return {
            width: domNode.getAttribute('data-width') || domNode.style.width,
            align: domNode.getAttribute('data-align') || undefined,
        };
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    constructor(scroll: any, domNode: Node) {
        super(scroll, domNode);
    }

    format(name: string, value: unknown): void {
        if (name === 'textbox') {
            if (typeof value === 'object' && value !== null) {
                const config = value as TextBoxBlotFormats;
                const domNode = this.domNode as HTMLElement;
                if (config.width) {
                    domNode.style.width = config.width;
                    domNode.setAttribute('data-width', config.width);
                }
                if (config.align !== undefined) {
                    // Remove old alignment classes
                    domNode.classList.remove(
                        'ql-textbox-align-left',
                        'ql-textbox-align-center',
                        'ql-textbox-align-right'
                    );
                    if (config.align) {
                        domNode.setAttribute('data-align', config.align);
                        domNode.classList.add(`ql-textbox-align-${config.align}`);
                    } else {
                        domNode.removeAttribute('data-align');
                    }
                }
            }
        } else {
            throw new Error(`${this.statics.name}.format: Unsupported format name '${name}'`);
        }
    }

    formats(): { [index: string]: TextBoxBlotFormats } {
        return { [this.statics.blotName]: TextBoxBlot.formats(this.domNode as HTMLElement) };
    }

    /**
     * Optimize maintains textbox structure and consistency.
     * - Ensures at least one child block exists (empty textboxes get a placeholder)
     * - Synchronizes textbox ID to match first child
     * - Wraps any non-allowed children in TextBoxBlock
     * 
     * Note: Does NOT merge textboxes with different IDs (see checkMerge)
     */
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    optimize(contextOrMutations: Record<string, unknown> | MutationRecord[], context?: Record<string, unknown>): void {
        // Handle both signatures: optimize(context) and optimize(mutations, context)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        super.optimize(contextOrMutations as any);
        
        // Ensure we have at least one child block
        if (this.children.length === 0) {
            const block = this.scroll.create(TextBoxBlock.blotName, this.textboxId) as Block;
            this.appendChild(block);
        }

        const firstChild = this.children.head as TextBoxBlock | TextBoxTable;
        if (!firstChild) return;

        // Ensure all direct children are allowed types
        this.children.forEach((child) => {
            const allowed = TextBoxBlot.allowedChildren?.some(
                (ChildClass) => child instanceof ChildClass
            );
            if (!allowed) {
                // Wrap disallowed children in a TextBoxBlock
                const block = this.scroll.create(TextBoxBlock.blotName, this.textboxId) as Block;
                child.replaceWith(block);
                block.appendChild(child);
            }
        });

        this.children.forEach((child) => {
            if (child.next == null) return;
            const childId = (child as TextBoxBlock | TextBoxTable).getTextBoxId();
            const nextId = (child.next as TextBoxBlock | TextBoxTable).getTextBoxId();
            if (childId !== nextId) {
                const next = this.splitAfter(child);
                if (next) {
                    next.optimize({});
                }
                // if (this.prev) {
                //     this.prev.optimize({});
                // }
            }
        });
    }

    /**
     * Prevent merging textboxes with different IDs.
     * This is critical for side-by-side textbox layout - without this check,
     * consecutive textboxes would merge into one during optimize.
     * 
     * Similar to table row implementation where rows with different IDs stay separate.
     */
    checkMerge(): boolean {
        if (super.checkMerge() && this.next instanceof TextBoxBlot) {
            const id = (this.next.children.head as TextBoxBlock | TextBoxTable).getTextBoxId();
            return this.textboxId === id;
        }
        return false;
    }
}

// TextBoxBreak.requiredContainer = TextBoxBlot;
// TextBoxSoftBreak.requiredContainer = TextBoxBlot;
TextBoxBlock.requiredContainer = TextBoxBlot;

/**
 * TextBoxFormatter Module - Provides resize and alignment functionality for TextBox blots
 * 
 * Features:
 * - Visual overlay with resize handles on all four corners
 * - Alignment toolbar with left/center/right buttons
 * - Click-to-select textbox for editing
 * - Dynamic repositioning when content changes or alignment is applied
 * - Supports float-based side-by-side layout (left/right alignments)
 * 
 * Alignment behavior:
 * - Left: Float left with right margin, allows text wrapping on right side
 * - Right: Float right with left margin, allows text wrapping on left side
 * - Center: Block display with auto margins, no float
 * 
 * Based on @enzedonline/quill-blot-formatter2 with customizations for TextBox blots.
 */
class TextBoxFormatter {
    quill: Quill;
    options: {
        debug?: boolean;
        overlay?: {
            className?: string;
            style?: Record<string, string>;
        };
        resize?: {
            handleClassName?: string;
            handleStyle?: Record<string, string>;
        };
        align?: {
            alignments?: string[];
            icons?: Record<string, string>;
        };
        toolbar?: {
            mainClassName?: string;
            buttonClassName?: string;
        };
    };
    overlay: HTMLElement;
    toolbar: HTMLElement;
    currentTarget: HTMLElement | null;
    resizeHandles: {
        topLeft: HTMLElement;
        topRight: HTMLElement;
        bottomLeft: HTMLElement;
        bottomRight: HTMLElement;
    };
    alignButtons: Record<string, HTMLElement>;
    isDragging: boolean;
    dragHandle: HTMLElement | null;
    dragStartX: number;
    dragStartWidth: number;

    constructor(quill: Quill, options: Record<string, unknown> = {}) {
        this.quill = quill;
        this.options = deepmerge({
            debug: false,
            overlay: {
                className: 'ql-textbox-overlay',
                style: {}
            },
            resize: {
                handleClassName: 'ql-textbox-handle',
                handleStyle: {
                    width: '12px',
                    height: '12px',
                    backgroundColor: '#4285f4',
                    border: '1px solid white'
                }
            },
            align: {
                alignments: ['left', 'center', 'right'],
                icons: {
                    left: '⬅',
                    center: '↔',
                    right: '➡'
                }
            },
            toolbar: {
                mainClassName: 'ql-textbox-toolbar',
                buttonClassName: 'ql-textbox-toolbar-button'
            }
        }, options, {
            // Replace arrays instead of concatenating them
            arrayMerge: (_destinationArray, sourceArray) => sourceArray
        });

        this.overlay = this.createOverlay();
        this.toolbar = this.createToolbar();
        this.currentTarget = null;
        this.resizeHandles = this.createResizeHandles();
        this.alignButtons = {};
        this.isDragging = false;
        this.dragHandle = null;
        this.dragStartX = 0;
        this.dragStartWidth = 0;

        this.attachEventListeners();
        this.log('TextBoxFormatter initialized');
    }

    log(...args: unknown[]): void {
        if (this.options.debug) {
            console.debug('[TextBoxFormatter]', ...args);
        }
    }

    createOverlay(): HTMLElement {
        const overlay = document.createElement('div');
        overlay.className = this.options.overlay.className;
        overlay.style.cssText = `
            position: absolute;
            display: none;
            border: 2px dashed #4285f4;
            pointer-events: none;
            z-index: 100;
        `;
        Object.assign(overlay.style, this.options.overlay.style || {});
        this.quill.root.parentNode.appendChild(overlay);
        return overlay;
    }

    createToolbar(): HTMLElement {
        const toolbar = document.createElement('div');
        toolbar.className = this.options.toolbar.mainClassName;
        toolbar.style.cssText = `
            position: absolute;
            display: none;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px;
            z-index: 101;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        `;
        this.quill.root.parentNode.appendChild(toolbar);
        return toolbar;
    }

    createResizeHandles(): {
        topLeft: HTMLElement;
        topRight: HTMLElement;
        bottomLeft: HTMLElement;
        bottomRight: HTMLElement;
    } {
        const positions = [
            { name: 'topLeft', cursor: 'nwse-resize', pos: { top: '-6px', left: '-6px' } },
            { name: 'topRight', cursor: 'nesw-resize', pos: { top: '-6px', right: '-6px' } },
            { name: 'bottomLeft', cursor: 'nesw-resize', pos: { bottom: '-6px', left: '-6px' } },
            { name: 'bottomRight', cursor: 'nwse-resize', pos: { bottom: '-6px', right: '-6px' } }
        ];

        const handles: Record<string, HTMLElement> = {};

        positions.forEach(({ name, cursor, pos }) => {
            const handle = document.createElement('div');
            handle.className = this.options.resize.handleClassName;
            handle.setAttribute('data-position', name);
            handle.style.cssText = `
                position: absolute;
                cursor: ${cursor};
                pointer-events: auto;
                border-radius: 50%;
            `;
            Object.assign(handle.style, pos);
            Object.assign(handle.style, this.options.resize.handleStyle || {});
            this.overlay.appendChild(handle);
            handles[name] = handle;
        });

        return handles as {
            topLeft: HTMLElement;
            topRight: HTMLElement;
            bottomLeft: HTMLElement;
            bottomRight: HTMLElement;
        };
    }

    createAlignButtons(): void {
        this.toolbar.innerHTML = '';
        this.alignButtons = {};

        this.options.align.alignments.forEach((alignment) => {
            const button = document.createElement('button');
            button.className = this.options.toolbar.buttonClassName;
            button.setAttribute('data-action', alignment);
            button.innerHTML = this.options.align.icons[alignment] || alignment[0].toUpperCase();
            button.style.cssText = `
                padding: 6px 10px;
                margin: 0 2px;
                border: 1px solid #ddd;
                background: white;
                cursor: pointer;
                border-radius: 3px;
            `;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.applyAlignment(alignment);
            });
            this.toolbar.appendChild(button);
            this.alignButtons[alignment] = button;
        });
    }

    /**
     * Attach event listeners for textbox selection, click-away hide, scroll,
     * and dynamic repositioning on text changes.
     * 
     * Key behaviors:
     * - Click textbox to select and show overlay
     * - Click outside to deselect and hide overlay
     * - Text changes trigger overlay repositioning (via text-change event)
     * - Scroll triggers repositioning to keep overlay aligned
     */
    attachEventListeners(): void {
        // Click on textbox to show overlay
        this.quill.root.addEventListener('click', (e: MouseEvent) => {
            const target = (e.target as HTMLElement).closest('.ql-textbox');
            if (target && target instanceof HTMLElement) {
                e.preventDefault();
                this.show(target);
            } else {
                this.hide();
            }
        });

        // Handle resize
        Object.values(this.resizeHandles).forEach((handle) => {
            handle.addEventListener('mousedown', (e: MouseEvent) => {
                e.preventDefault();
                e.stopPropagation();
                this.startResize(e, handle);
            });
        });

        // Hide on outside click
        document.addEventListener('mousedown', (e: MouseEvent) => {
            if (this.currentTarget &&
                !this.overlay.contains(e.target as Node) &&
                !this.toolbar.contains(e.target as Node) &&
                !(e.target as HTMLElement).closest('.ql-textbox')) {
                this.hide();
            }
        });

        // Hide on scroll
        this.quill.root.addEventListener('scroll', () => {
            if (this.currentTarget) {
                this.repositionOverlay();
            }
        });

        // Reposition overlay when text changes (user typing affects textbox size)
        // Use requestAnimationFrame to ensure DOM updates complete before repositioning
        this.quill.on('text-change', () => {
            if (this.currentTarget) {
                // Use requestAnimationFrame to ensure DOM has updated
                requestAnimationFrame(() => {
                    this.repositionOverlay();
                });
            }
        });
    }

    show(target: HTMLElement): void {
        this.currentTarget = target;
        this.createAlignButtons();
        this.updateAlignButtons();
        this.repositionOverlay();
        this.overlay.style.display = 'block';
        this.toolbar.style.display = 'block';
        this.log('Showing overlay for', target);
    }

    hide(): void {
        if (this.isDragging) return;
        this.currentTarget = null;
        this.overlay.style.display = 'none';
        this.toolbar.style.display = 'none';
        this.log('Hiding overlay');
    }

    repositionOverlay(): void {
        if (!this.currentTarget) return;

        const rect = this.currentTarget.getBoundingClientRect();
        const editorRect = this.quill.root.getBoundingClientRect();

        this.overlay.style.left = `${rect.left - editorRect.left + this.quill.root.scrollLeft}px`;
        this.overlay.style.top = `${rect.top - editorRect.top + this.quill.root.scrollTop}px`;
        this.overlay.style.width = `${rect.width}px`;
        this.overlay.style.height = `${rect.height}px`;

        // Position toolbar above the textbox
        this.toolbar.style.left = `${rect.left - editorRect.left + this.quill.root.scrollLeft}px`;
        this.toolbar.style.top = `${rect.top - editorRect.top + this.quill.root.scrollTop - 40}px`;
    }

    startResize(e: MouseEvent, handle: HTMLElement): void {
        if (!this.currentTarget) return;

        this.isDragging = true;
        this.dragHandle = handle;
        this.dragStartX = e.clientX;
        this.dragStartWidth = this.currentTarget.offsetWidth;

        const onMouseMove = (moveEvent: MouseEvent) => {
            if (!this.isDragging || !this.currentTarget) return;

            const deltaX = moveEvent.clientX - this.dragStartX;
            const position = this.dragHandle.getAttribute('data-position');

            let newWidth = this.dragStartWidth;
            if (position.includes('Right')) {
                newWidth = this.dragStartWidth + deltaX;
            } else if (position.includes('Left')) {
                newWidth = this.dragStartWidth - deltaX;
            }

            // Constrain width
            const editorWidth = this.quill.root.offsetWidth;
            newWidth = Math.max(100, Math.min(newWidth, editorWidth));

            // Calculate percentage or pixel width
            const isRelative = this.currentTarget.getAttribute('data-width')?.includes('%');
            const widthValue = isRelative
                ? `${(newWidth / editorWidth * 100).toFixed(2)}%`
                : `${newWidth}px`;

            this.currentTarget.style.width = widthValue;
            this.currentTarget.setAttribute('data-width', widthValue);
            this.repositionOverlay();
            this.log('Resizing to', widthValue);
        };

        const onMouseUp = () => {
            this.isDragging = false;
            this.dragHandle = null;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            this.updateBlotFormat();
            this.log('Resize complete');
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    updateAlignButtons(): void {
        if (!this.currentTarget) return;

        const currentAlign = this.currentTarget.getAttribute('data-align') || '';
        Object.entries(this.alignButtons).forEach(([alignment, button]) => {
            if (alignment === currentAlign) {
                button.style.background = '#e3f2fd';
                button.style.borderColor = '#4285f4';
            } else {
                button.style.background = 'white';
                button.style.borderColor = '#ddd';
            }
        });
    }

    /**
     * Apply alignment to the selected textbox.
     * - Left/Right: Uses CSS float for side-by-side layout
     * - Center: Uses block display with auto margins
     * - Toggle: Clicking same alignment removes it
     * 
     * After applying, repositions overlay to match new size/position
     * (float can change dimensions).
     */
    applyAlignment(alignment: string): void {
        if (!this.currentTarget) return;

        // Remove old alignment classes
        this.currentTarget.classList.remove(
            'ql-textbox-align-left',
            'ql-textbox-align-center',
            'ql-textbox-align-right'
        );

        // Toggle alignment
        const currentAlign = this.currentTarget.getAttribute('data-align');
        if (currentAlign === alignment) {
            // Clear alignment
            this.currentTarget.removeAttribute('data-align');
        } else {
            // Apply new alignment
            this.currentTarget.setAttribute('data-align', alignment);
            this.currentTarget.classList.add(`ql-textbox-align-${alignment}`);
        }

        this.updateAlignButtons();
        this.updateBlotFormat();
        
        // Reposition overlay after alignment changes (float can change size/position)
        requestAnimationFrame(() => {
            this.repositionOverlay();
        });
        
        this.log('Applied alignment', alignment);
    }

    updateBlotFormat(): void {
        if (!this.currentTarget) return;

        const blot = Quill.find(this.currentTarget) as Blot;
        if (blot && blot.statics.blotName === 'textbox') {
            const index = this.quill.getIndex(blot);
            const formats = TextBoxBlot.formats(this.currentTarget);
            this.quill.formatText(index, 1, 'textbox', formats, 'user');
            this.log('Updated blot format', formats);
        }
    }
}

// ============= End TextBox Implementation =============

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const NextTableModule = Quill.import("modules/table") as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const NextTableCell = Quill.import("formats/table") as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const NextTableRow = Quill.import("formats/table-row") as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const NextTableContainer = Quill.import("formats/table-container") as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const TableBody = Quill.import("formats/table-body") as any;


export class TableCell extends NextTableCell {
    static create(value: string | null | { row: string; class?: string }): HTMLElement {
        let node: HTMLElement;
        if (typeof value === "string" || value == null) {
            node = super.create(value);
        } else {
            node = super.create(value.row);

            if (value.class) {
                node.setAttribute("class", value.class);
            }
        }
        return node;
    }

    static formats(domNode: HTMLElement, scroll: unknown): { row?: string; class?: string } {
        const formats: { row?: string; class?: string } = {};
        formats.row = super.formats(domNode, scroll);
        if (domNode.hasAttribute("class")) {
            const klass = domNode.getAttribute("class");
            if (klass && klass.length) formats.class = klass;
        }
        return formats;
    }

    formats(): { [index: string]: { row?: string; class?: string } } {
        return { [this.statics.blotName]: TableCell.formats(this.domNode, this.scroll) };
    }

    format(name: string, value: string | { row?: string; class?: string } | null): void {
        if (name === this.statics.blotName) {
            if (typeof value === "string") {
                // super.format(name, value);
                throw new Error(`${this.statics.name}.format: string value is not supported, use an object { row?: string, class?: string }`);
            } else
            if (typeof value === "object" && value != null) {
                if (value.row) super.format(name, value.row);
                if (value.class && value.class.length) {
                    this.domNode.setAttribute("class", value.class);
                } else {
                    if (this.domNode.hasAttribute("class"))
                        this.domNode.removeAttribute("class");
                }
            }
        } else {
            super.format(name, value);
        }
    }
}


export class TableRow extends NextTableRow {
    static create(value?: string | null): HTMLElement {
        const node = super.create() as HTMLElement;
        if (value && value.length) {
            node.setAttribute("class", value);
        }
        return node;
    }

    static formats(domNode: HTMLElement): string | undefined {
        if (domNode.hasAttribute("class")) {
            return domNode.getAttribute("class");
        }
        return undefined;
    }

    formats() {
        return { [this.statics.blotName]: TableRow.formats(this.domNode) };
    }


    /**
     * Allow:
     * - row.format('table-row', 'my-class')  // convenience (treat 'table-row' as class setter)
     */
    format(name: string, value: string | null | undefined): void {
        if (name === this.statics.blotName) {
            if (value && value.length)
                this.domNode.setAttribute("class", value)
            else this.domNode.removeAttribute("class");
        } else {
            throw new Error(`${this.statics.name}.format: Unsupported format name '${name}'`);
        }
    }

    checkMerge() {
        if (Container.prototype.checkMerge.call(this) && this.next.children.head != null) {
            const childName = this.children.head.statics.blotName;
            const thisHead = this.children.head.formats();
            const thisTail = this.children.tail.formats();
            const nextHead = this.next.children.head.formats();
            const nextTail = this.next.children.tail.formats();
            return (
                thisHead[childName].row === thisTail[childName].row &&
                thisHead[childName].row === nextHead[childName].row &&
                thisHead[childName].row === nextTail[childName].row
            );
        }
        return false;
    }

    optimize(...args: unknown[]): void {
        Container.prototype.optimize.call(this, ...args);
        const isTextBox = this instanceof TextBoxTableRow;
        const Cell = isTextBox ? TextBoxTableCell : TableCell;
        this.children.forEach((child: TableCell | TextBoxTableCell) => {
            if (child.next == null) return;
            const childFormats = child.formats();
            const nextFormats = child.next.formats();
            // if (childFormats.table !== nextFormats.table) {
            if (childFormats[Cell.blotName]?.row !== nextFormats[Cell.blotName]?.row) {
                const next = this.splitAfter(child);
                if (next) {
                    next.optimize();
                }
                // We might be able to merge with prev now
                if (this.prev) {
                    this.prev.optimize();
                }
            }
        });
    }
}


export class TableContainer extends NextTableContainer {

    static create(value?: string | null): HTMLElement {
        const node = super.create(value) as HTMLElement;
        if (value && value.length) {
            node.setAttribute("class", value);
        }
        return node;
    }

    static formats(domNode: HTMLElement): string | { class?: string; textbox_id?: string } | undefined {
        if (domNode.hasAttribute("class")) {
            return domNode.getAttribute("class");
        }
        return undefined;
    }

    formats() {
        return { [this.statics.blotName]: TableContainer.formats(this.domNode) };
    }

    format(name: string, value: string | null | undefined): void {
        if (name === this.statics.blotName) {
            if (value && value.length) {
                this.domNode.setAttribute("class", value);
            } else {
                this.domNode.removeAttribute("class");
            }
        } else {
            throw new Error(`${this.statics.name}.format: Unsupported format name '${name}'`);
        }
    }

    balanceCells() {
        const rows = this.descendants(TableRow);
        const maxColumns = rows.reduce((max, row) => {
            return Math.max(row.children.length, max);
        }, 0);
        const isTextBox = rows[0] instanceof TextBoxTableRow;
        const Cell = isTextBox ? TextBoxTableCell : TableCell;
        rows.forEach((row) => {
            new Array(maxColumns - row.children.length).fill(0).forEach(() => {
                let value = null;
                if (row.children.head != null) {
                    value = Cell.formats(row.children.head.domNode, this.scroll);
                }
                // Pass an object so the new cell keeps both data-row and class
                const blot = this.scroll.create(Cell.blotName, value);
                row.appendChild(blot);
                blot.optimize(); // Add break blot
            });
        });
    }

    insertColumn(index: number) {
        const [body] = this.descendant(TableBody);
        if (body == null || body.children.head == null) return;
        const isTextBox = body instanceof TextBoxTableBody;
        const Cell = isTextBox ? TextBoxTableCell : TableCell;
        body.children.forEach((row: TableRow | TextBoxTableRow) => {
            const ref = row.children.at(index);
            const value = Cell.formats(row.children.head.domNode, this.scroll);
            const cell = this.scroll.create(Cell.blotName, value);
            row.insertBefore(cell, ref);
        });
    }

    insertRow(index: number) {
        const [body] = this.descendant(TableBody);
        if (body == null || body.children.head == null) return;
        const isTextBox = body instanceof TextBoxTableBody;
        const id = tableId();
        // copy row classes from first body row if present
        const templateRow = body.children.head;
        const templateRowClass = templateRow && templateRow.domNode ? templateRow.domNode.getAttribute('class') : undefined;
        let rowClass: string;
        if (templateRowClass && templateRowClass.length)
            rowClass = templateRowClass;
        const row = this.scroll.create(isTextBox ? TextBoxTableRow.blotName : TableRow.blotName, rowClass);
        body.children.head.children.forEach(() => {
            // preserve classes on created cells from the template cell
            const headCell = templateRow.children.head;
            const cellFormats = Object.values(headCell.formats())[0] as { class?: string; row?: string; textbox_id?: string; };
            cellFormats.row = id;
            const cell = this.scroll.create(isTextBox ? TextBoxTableCell.blotName : TableCell.blotName, cellFormats);
            row.appendChild(cell);
        });
        const ref = body.children.at(index);
        body.insertBefore(row, ref);
    }
}


export class TableModule extends NextTableModule {

    getTable(
        range = this.quill.getSelection(),
    ): [null, null, null, -1] | [TableContainer | TextBoxTable, TableRow | TextBoxTableRow, TableCell | TextBoxTableCell, number] {
        if (range == null) return [null, null, null, -1];
        const [cell, offset] = this.quill.getLine(range.index);
        if (cell == null || (cell.statics.blotName !== TableCell.blotName && cell.statics.blotName !== TextBoxTableCell.blotName)) {
            return [null, null, null, -1];
        }
        const row = cell.parent;
        const table = row.parent.parent;
        return [table, row, cell, offset];
    }

    insertTable(rows: number, columns: number) {
        const range = this.quill.getSelection();
        if (range == null) return;

        let [ item ] = this.quill.getLine(range.index);
        let blotName = 'table';
        const properties: { row?: string; textbox_id?: string; } = {};
        while (item != null) {
            if (item instanceof TextBoxBlot) {
                blotName = 'textbox-table-cell';
                properties.textbox_id = item.textboxId;
                break;
            }
            item = item.parent;
        }

        const delta = new Array(rows).fill(0).reduce((memo) => {
          const text = new Array(columns).fill('\n').join('');
          return memo.insert(text, {[blotName]: Object.assign({}, properties, {row: tableId()})});
        }, new Delta().retain(range.index));
        this.quill.updateContents(delta, Quill.sources.USER);
        this.quill.setSelection(range.index, Quill.sources.SILENT);
        this.balanceTables();
    }
}


export class TextBoxTableCell extends TableCell {
    static blotName = 'textbox-table-cell';
    static className = 'ql-textbox-table-cell';
    static requiredContainer: typeof TextBoxTableRow;

    static create(value?: string | null | { class?: string; row?: string; textbox_id?: string; }): HTMLElement {
        if (typeof value === 'object' && value != null) {
            let classValue: string | null = null;
            let rowValue: string | null = null;
            let textboxId: string | null = null;
            
            if (value.class) {
                classValue = value.class;
            }
            if (value.row) {
                rowValue = value.row;
            }
            if (value.textbox_id) {
                textboxId = value.textbox_id;
            }
            
            const node = super.create({ row: rowValue || '', class: classValue || '' }) as HTMLElement;
            if (textboxId) {
                node.setAttribute('data-textbox-id', textboxId);
            }
            return node;
        }
        const node = super.create(value as null | string) as HTMLElement;
        return node;
    }

    static formats(domNode: HTMLElement, scroll: unknown): { row?: string; class?: string; textbox_id?: string } {
        const formats: { row?: string; class?: string; textbox_id?: string } = {};
        const baseFormats = super.formats(domNode, scroll);
        formats.row = baseFormats.row;
        if (baseFormats.class) {
            formats.class = baseFormats.class;
        }
        if (domNode.hasAttribute('data-textbox-id')) {
            const textboxId = domNode.getAttribute('data-textbox-id');
            if (textboxId && textboxId.length) formats.textbox_id = textboxId;
        }
        return formats;
    }

    formats(): { [index: string]: { row?: string; class?: string; textbox_id?: string } } {
        return { [this.statics.blotName]: TextBoxTableCell.formats(this.domNode, this.scroll) };
    }

    format(name: string, value: string | { row?: string; class?: string; textbox_id?: string } | null): void {
        if (name === this.statics.blotName) {
            if (typeof value === 'string') {
                throw new Error(`${this.statics.name}.format: string value is not supported, use an object { row?: string; class?: string; textbox_id?: string }`);
            } else
            if (typeof value === 'object' && value != null) {
                if (value.row) {
                    this.domNode.setAttribute('data-row', value.row);
                }
                if (value.class && value.class.length) {
                    this.domNode.setAttribute('class', value.class);
                } else {
                    if (this.domNode.hasAttribute('class'))
                        this.domNode.removeAttribute('class');
                }
                if (value.textbox_id && value.textbox_id.length) {
                    this.domNode.setAttribute('data-textbox-id', value.textbox_id);
                } else {
                    if (this.domNode.hasAttribute('data-textbox-id'))
                        this.domNode.removeAttribute('data-textbox-id');
                }
            }
        } else {
            super.format(name, value);
        }
    }
}


export class TextBoxTableRow extends TableRow {
    static blotName = 'textbox-table-row';
    static className = 'ql-textbox-table-row';
    static requiredContainer: typeof TextBoxTableBody;
    static allowedChildren: BlotConstructor[];
}

class TextBoxTableBody extends TableBody {
    static blotName = 'textbox-table-body';
    static className = 'ql-textbox-table-body';
    static requiredContainer: typeof TextBoxTable;
}


export class TextBoxTable extends TableContainer {
    static blotName = 'textbox-table';
    static className = 'ql-textbox-table';
    static requiredContainer: typeof TextBoxBlot = TextBoxBlot;
    static allowedChildren: BlotConstructor[];

    // static create(value?: string | { class?: string; textbox_id?: string; } | null): HTMLElement {
    //     let classValue: string | null = null;
    //     let textboxId: string | null = null;
        
    //     if (typeof value === 'string') {
    //         classValue = value;
    //     } else if (value && typeof value === 'object') {
    //         classValue = value.class || null;
    //         textboxId = value.textbox_id || null;
    //     }
        
    //     const node = super.create(classValue) as HTMLElement;
    //     if (textboxId) {
    //         node.setAttribute('data-textbox-id', textboxId);
    //     }
    //     return node;
    // }

    // static formats(domNode: HTMLElement): { class?: string; textbox_id?: string } {
    //     const formats: { class?: string; textbox_id?: string } = {};
    //     if (domNode.hasAttribute('class')) {
    //         const klass = domNode.getAttribute('class');
    //         if (klass && klass.length) formats.class = klass;
    //     }
    //     if (domNode.hasAttribute('data-textbox-id')) {
    //         const textboxId = domNode.getAttribute('data-textbox-id');
    //         if (textboxId && textboxId.length) formats.textbox_id = textboxId;
    //     }
    //     return formats;
    // }

    getTextBoxId(): string | null {
        const [cell] = this.descendant(TextBoxTableCell);
        if (cell && cell.domNode.hasAttribute('data-textbox-id')) {
            return cell.domNode.getAttribute('data-textbox-id');
        }
        return null;
    }

    // formats() {
    //     return { [this.statics.blotName]: TextBoxTable.formats(this.domNode) };
    // }

    // format(name: string, value: string | null | undefined | { class?: string; textbox_id?: string; }): void {
    //     if (name === this.statics.blotName) {
    //         if (typeof value === 'string') {
    //             throw new Error(`Invalid format type (type 'string') expected '{ class?: string; textbox_id?: string; }'`);
    //         } else if (typeof value === 'object' && value != null) {
    //             super.format(name, value.class);
    //             if (value.textbox_id) {
    //                 this.domNode.setAttribute('data-textbox-id', value.textbox_id);
    //             } else {
    //                 this.domNode.removeAttribute('data-textbox-id');
    //             }
    //         }
    //     } else {
    //         throw new Error(`TextBoxTable.format: Unsupported format name '${name}'`);
    //     }
    // }
}


TextBoxTableCell.requiredContainer = TextBoxTableRow;
TextBoxTableRow.allowedChildren = [TextBoxTableCell as unknown as BlotConstructor];

TextBoxTableRow.requiredContainer = TextBoxTableBody;
TextBoxTableBody.allowedChildren = [TextBoxTableRow as unknown as BlotConstructor];

TextBoxTableBody.requiredContainer = TextBoxTable;
TextBoxTable.allowedChildren = [TextBoxTableBody as unknown as BlotConstructor];

// TextBoxTable.requiredContainer = TextBoxBlot;

TextBoxBlot.allowedChildren = [TextBoxBlock, TextBoxTable as unknown as BlotConstructor];

Quill.register('formats/textbox-table', TextBoxTable);
Quill.register('formats/textbox-table-body', TextBoxTableBody);
Quill.register('formats/textbox-table-row', TextBoxTableRow);
Quill.register('formats/textbox-table-cell', TextBoxTableCell);


Quill.register('modules/imageDropAndPaste', QuillImageDropAndPaste);
Quill.register('modules/blotFormatter2', BlotFormatter);
Quill.register({"blots/mention": MentionBlot, "modules/mention": Mention});
Quill.register('modules/htmlEditButton', htmlEditButton);

// Register TextBox blot and formatter
Quill.register('formats/textbox', TextBoxBlot);
Quill.register('formats/textbox-block', TextBoxBlock);
// Quill.register('formats/textbox-soft-break', TextBoxSoftBreak);
// Quill.register('formats/textbox-break', TextBoxBreak);
Quill.register('modules/textboxFormatter', TextBoxFormatter);

Quill.register('modules/table', TableModule);
Quill.register('formats/table-row', TableRow);
Quill.register('formats/table', TableCell);
Quill.register('formats/table-container', TableContainer);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const QuillImageData: any = QuillImageDropAndPaste.ImageData;

let ex: ImportPool; const exModulePromises = ex = {
    AbortController: import(/* webpackChunkName: "AbortController_quillmodules" */"abort-controller"),
    prContextMenu: import(/* webpackChunkName: "prContextMenu_quillmodules" */"primereact/contextmenu"),
    prUtils: import(/* webpackChunkName: "prUtils_quillmodules" */"primereact/utils"),
    queryString:  import(/* webpackChunkName: "queryString_quillmodules" */"query-string"),
    i18n: import(/* webpackChunkName: "i18n_quillmodules" */"./i18n"),
    u: import(/* webpackChunkName: "LinoUtils_quillmodules" */"./LinoUtils"),
};RegisterImportPool(ex);


export const tableContextMenuProps = ({i18n, quillRef, c}) => {
    const module = () => {
        quillRef.current.focus();
        return quillRef.current.getModule("table");
    }

    const model = [
        {
            command: () => {
                module().insertColumnLeft();
            },
            icon: <span>&nbsp;⭰&nbsp;</span>,
            label: i18n.t("Insert column left"),
        },
        {
            command: () => {
                module().insertColumnRight();
            },
            icon: <span>&nbsp;⭲&nbsp;</span>,
            label: i18n.t("Insert column right"),
        },
        {
            command: () => {
                module().insertRowAbove();
            },
            icon:  <span>&nbsp;⭱&nbsp;</span>,
            label: i18n.t("Insert row above"),
        },
        {
            command: () => {
                module().insertRowBelow();
            },
            icon: <span>&nbsp;⭳&nbsp;</span>,
            label: i18n.t("Insert row below"),
        },
        {
            command: () => {
                module().deleteColumn();
            },
            icon: "pi pi-delete-left",
            label: i18n.t("Delete column"),
        },
        {
            command: () => {
                module().deleteRow();
            },
            icon: "pi pi-eraser",
            label: i18n.t("Delete row"),
        },
        {
            command: () => {
                module().deleteTable();
            },
            icon: "pi pi-trash",
            label: i18n.t("Delete table"),
        },
        {
            command: () => {
                const quill = quillRef.current;
                const [table, row, cell] = module().getTable();
                const ctx = c;
                const tableClasses = i18n.t("TABLE class"),
                    rowClasses = i18n.t("TR class"),
                    cellClasses = i18n.t("TD class"),
                    applyToAllRow = i18n.t("Apply to all rows"),
                    applyToAllCell = i18n.t("Apply to all cells"),
                    applyToAllCellOfThisRow = i18n.t("Apply to all cells of this row"),
                    title = i18n.t("Manage classes"),
                    agreeLabel = i18n.t("Apply");

                const ok = (data) => {
                    const tcs = data[tableClasses].split(",")
                        .filter(item => !!item).join(" ").trim();

                    quill.formatLine(quill.getIndex(table), 1, table.statics.blotName, tcs);

                    const formatRow = (classes, row) => {
                        quill.formatLine(quill.getIndex(row), 1, row.statics.blotName, classes);
                    }

                    const rcs = data[rowClasses].split(",")
                    .filter(item => !!item).join(" ").trim();

                    formatRow(rcs, row);
                    let _row;
                    if (data[applyToAllRow]) {
                        _row = row.prev;
                        while (_row !== null) {
                            formatRow(rcs, _row);
                            _row = _row.prev;
                        }
                        _row = row.next;
                        while (_row !== null) {
                            formatRow(rcs, _row);
                            _row = _row.next;
                        }
                    }

                    const allCell = data[applyToAllCell];
                    let _cell;
                    const ccs = data[cellClasses].split(",")
                        .filter(item => !!item).join(" ").trim();

                    const formatCellLine = (classes, cell) => {
                        const blotName = cell.statics.blotName;
                        const existingFormats = cell.formats()[blotName];
                        quill.formatLine(quill.getIndex(cell), 1, blotName, Object.assign({}, existingFormats, {class: classes}));
                    }

                    formatCellLine(ccs, cell);

                    if (allCell || data[applyToAllCellOfThisRow]) {
                        _cell = cell.prev;
                        while (_cell !== null) {
                            formatCellLine(ccs, _cell);
                            _cell = _cell.prev;
                        }
                        _cell = cell.next;
                        while (_cell !== null) {
                            formatCellLine(ccs, _cell);
                            _cell = _cell.next;
                        }
                    }

                    if (allCell) {
                        _row = row.prev;
                        while (_row !== null) {
                            _cell = _row.children.head;
                            if (_cell.prev !== null) {
                                throw new Error("Programming error, row.children.head returned cell with prev item")
                            }
                            while (_cell !== null) {
                                formatCellLine(ccs, _cell);
                                _cell = _cell.next;
                            }
                            _row = _row.prev;
                        }

                        _row = row.next;
                        while (_row !== null) {
                            _cell = _row.children.head;
                            if (_cell.prev !== null) {
                                throw new Error("Programming error, row.children.head returned cell with prev item")
                            }
                            while (_cell !== null) {
                                formatCellLine(ccs, _cell);
                                _cell = _cell.next;
                            }
                            _row = _row.next;
                        }
                    }
                    quill.emitter.emit('text-change');
                    return true;
                }

                ctx.APP.dialogFactory.createParamDialog(ctx, {
                    [tableClasses]: {
                        default: table.domNode.getAttribute("class") || "",
                        react_name: "CharFieldElement",
                    },
                    [rowClasses]: {
                        default: row.domNode.getAttribute("class") || "",
                        react_name: "CharFieldElement",
                    },
                    [applyToAllRow]: {
                        default: false,
                        react_name: "BooleanFieldElement",
                    },
                    [cellClasses]: {
                        default: cell.domNode.getAttribute("class") || "",
                        react_name: "CharFieldElement",
                    },
                    [applyToAllCellOfThisRow]: {
                        default: false,
                        react_name: "BooleanFieldElement",
                    },
                    [applyToAllCell]: {
                        default: false,
                        react_name: "BooleanFieldElement",
                    },
                }, title, ok, agreeLabel);
            },
            icon: <span>&nbsp;🄿&nbsp;</span>,  // \u1F13F
            label: i18n.t("Properties"),
        },
    ]
    return {model}
}


const onRightClick = ({plain, quillRef, elementRef}) => {
    if (plain) return null;
    return (e) => {
        const tableModule = quillRef.current.getModule("table");
        const [table] = tableModule.getTable();
        if (table !== null) {
            e.preventDefault();
            elementRef.current.show(e);
        }
    }
}


const onTextChange = (parent, plain, e) => {
    // console.log("onTextChange", e);
    // cleans up the trailing new line (\n)
    const plainValue = e.textValue.slice(0, -1);
    const value = (plain ? plainValue : e.htmlValue ) || "";
    parent.update({[parent.dataKey]: value});
    // elem.setState({})
}


export const getQuillModules = (
    {signal, i18n, props, quillRef}
) => {
    const { c } = props;
    const toolbarID = `l-ql-toolbar-${props.parent.props.elem.name}`;
    const modules: t.StringKeyedObject = {
        toolbar: `#${toolbarID}`,
        mention: quillMention({
            silentFetch: c.actionHandler.silentFetch,
            signal,
            mentionValues: c.mentionValues,
        }),
        blotFormatter2: {
            debug: false,
            resize: {
                useRelativeSize: true,
            },
            video: {
                registerBackspaceFix: false
            }
        },
        textboxFormatter: {
            debug: false,
            resize: {
                handleStyle: {
                    width: '12px',
                    height: '12px',
                    backgroundColor: '#4285f4',
                    border: '2px solid white'
                }
            },
            align: {
                alignments: ['left', 'center', 'right'],
                icons: {
                    left: '⬅',
                    center: '↔',
                    right: '➡'
                }
            }
        },
        table: true,
    }
    if (props.showHeader) {
        modules.htmlEditButton = {
            msg: i18n.t('Edit HTML here, when you click "OK" the quill editor\'s contents will be replaced'),
            prependSelector: "div#raw-editor-container",
            okText: i18n.t("Ok"),
            cancelText: i18n.t("Cancel"),
            buttonTitle: i18n.t("Show HTML source"),
        }
    }
    if (props.c.APP.state.site_data.installed_plugins.includes('uploads'))
        modules.imageDropAndPaste = {handler: imageHandler(quillRef)};
    modules.keyboard = {
        bindings: {
            home: {
                key: "Home",
                shiftKey: null,
                handler: function (range, context) {
                    const quill = quillRef.current;
                    const [line] = quill.getLine(range.index);
                    if (line && line.domNode.tagName === "LI") {
                      // Move to the start of text inside the list item
                      if (context.event.shiftKey) {
                          const index = line.offset(quill.scroll);
                          quill.setSelection(index, range.index - index, Quill.sources.USER);
                      } else {
                          quill.setSelection(line.offset(quill.scroll), 0, Quill.sources.USER);
                      }
                      return false; // stop default browser behavior
                    }
                    return true;
                },
            },
        }
    }

    // Disable "- " from creating a bullet list or any other autofill.
    // https://github.com/slab/quill/blob/539cbffd0a13b18e9c65eb84dd35e6596e403158/packages/quill/src/modules/keyboard.ts#L550
    if (props.plain) modules.keyboard.bindings["list autofill"] = false;

    if (!props.showHeader) delete modules.toolbar;

    const meta = {toolbarID};

    return {modules, meta};
}


export const changeDelta = ({quillRef, parent, prUtils, plain}) => {
    return (delta, _oldContents, source) => {
        // copied from primereact/components/lib/editor/Editor.js
        const quill = quillRef.current;
        const firstChild = quill.container.children[0];
        let html = firstChild ? firstChild.innerHTML : null;
        const text = quill.getText();

        if (html === '<p><br></p>') {
            html = null;
        }

        // GitHub primereact #2271 prevent infinite loop on clipboard paste of HTML
        if (source === Quill.sources.API) {
            const htmlValue = quill.container.children[0];
            const editorValue = document.createElement('div');

            // editorValue.innerHTML = elem.props.urlParams.controller.dataContext.contextBackup || '';
            editorValue.innerHTML = parent.getValue() || '';

            // this is necessary because Quill rearranged style elements
            if (prUtils.DomHandler.isEqualElement(htmlValue, editorValue)) {
                return;
            }
        }

        // reorder attributes of the content to have a stable String representation
        if (html) {
            const div = document.createElement('div');
            div.innerHTML = html;
            function reorderAttributes(node) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    const attrs = Array.from(node.attributes) as Attr[];
                    attrs.sort((a, b) => a.name.localeCompare(b.name));
                    for (let i = 0; i < attrs.length; i++) {
                        node.removeAttribute(attrs[i].name);
                    }
                    for (let i = 0; i < attrs.length; i++) {
                        node.setAttribute(attrs[i].name, attrs[i].value);
                    }
                }
                for (let i = 0; i < node.childNodes.length; i++) {
                    reorderAttributes(node.childNodes[i]);
                }
            }
            reorderAttributes(div);
            html = div.innerHTML;

            // fix for quill inserting <br> instead of <br/>
            // html = html.replaceAll(/<br>/g, '<br/>');
        }

        onTextChange(parent, plain, {
            htmlValue: html,
            textValue: text,
            delta: delta,
            source: source
        });
    }
}


export const overrideImageButtonHandler = (quillRef) => {
    quillRef.current.getModule('toolbar').addHandler('image', (clicked) => {
        if (clicked) {
            // let fileInput;
            // fileInput = quill.container.querySelector('input.ql-image[type=file]');
            // if (fileInput == null) {
                const fileInput = document.createElement('input');
                fileInput.setAttribute('type', 'file');
                fileInput.setAttribute('accept', 'image/png, image/gif, image/jpeg, image/bmp, image/x-icon');
                fileInput.classList.add('ql-image');
                fileInput.addEventListener('change', (e) => {
                    const files = (e.target as HTMLInputElement).files;
                    let file;
                    if (files.length > 0) {
                        file = files[0];
                        const type = file.type;
                        const reader = new FileReader();
                        reader.onload = (e) => {
                            const dataURL = e.target.result;
                            imageHandler(quillRef)(
                                dataURL,
                                type,
                                new QuillImageData(dataURL, type, file.name)
                            );
                            fileInput.value = '';
                        }
                        reader.readAsDataURL(file);
                    }
                })
            // }
            fileInput.click();
        }
    })
}

export const imageHandler = (quillRef) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    return (imageDataURL, type, imageData) => {
        const quill = quillRef.current;
        let index = (quill.getSelection() || {}).index;
        if (index === undefined || index < 0) index = quill.getLength();
        quill.insertEmbed(index, 'image', imageDataURL);
        const imageBlot = quill.getLeaf(index)[0];
        imageBlot.domNode.setAttribute('width', '100%');
        imageBlot.domNode.setAttribute('height', 'auto');
    }
}

export const quillMention = ({silentFetch, signal, mentionValues}) => {
    function mentionSource(searchTerm, renderList, mentionChar) {
        if (searchTerm.length === 0) {
            const values = mentionValues[mentionChar];
            renderList(values, searchTerm);
        } else {
            ex.resolve(['queryString']).then(({queryString}) => {
                silentFetch({path: `suggestions?${queryString.default.stringify({
                    query: searchTerm, trigger: mentionChar})}`, signal: signal})
                .then(data => renderList(data.suggestions, searchTerm));
            });
        }
    }

    return {
        allowedChars: /^[A-Za-z0-9\s]*$/,
        mentionDenotationChars: window.App.state.site_data.suggestors,
        source: mentionSource,
        listItemClass: "ql-mention-list-item",
        mentionContainerClass: "ql-mention-list-container",
        mentionListClass: "ql-mention-list",
        dataAttributes: ["value", "link", "title", "denotationChar"],
    }
}

const quillToolbarHeaderTemplate = <React.Fragment>
    <span className="ql-formats">
        <select className='ql-header' defaultValue='0'>
            <option value='1'>Header 1</option>
            <option value='2'>Header 2</option>
            <option value='3'>Header 3</option>
            <option value='4'>Header 4</option>
            <option value='0'>Normal</option>
        </select>
        <select className='ql-font'>
            <option defaultValue="true"></option>
            <option value='serif'></option>
            <option value='monospace'></option>
        </select>
    </span>
    <span className="ql-formats">
        <select className="ql-size">
            <option value="small"></option>
            <option defaultValue="true"></option>
            <option value="large"></option>
            <option value="huge"></option>
        </select>
    </span>
    <span className="ql-formats">
        <button className="ql-script" value="sub"></button>
        <button className="ql-script" value="super"></button>
    </span>
    <span className="ql-formats">
        <button type='button' className='ql-bold' aria-label='Bold'></button>
        <button type='button' className='ql-italic' aria-label='Italic'></button>
        <button type='button' className='ql-underline' aria-label='Underline'></button>
    </span>
    <span className="ql-formats">
        <select className='ql-color'></select>
        <select className='ql-background'></select>
    </span>
    <span className="ql-formats">
        <button type='button' className='ql-list' value='ordered' aria-label='Ordered List'></button>
        <button type='button' className='ql-list' value='bullet' aria-label='Unordered List'></button>
        <select className='ql-align'>
            <option defaultValue="true"></option>
            <option value='center'></option>
            <option value='right'></option>
            <option value='justify'></option>
        </select>
    </span>
    <span className="ql-formats">
        <button type='button' className='ql-link' aria-label='Insert Link'></button>
        <button type='button' className='ql-image' aria-label='Insert Image'></button>
        <button type='button' className='ql-code-block' aria-label='Insert Code Block'></button>
    </span>
    <span className="ql-formats">
        <button type='button' className='ql-clean' aria-label='Remove Styles'></button>
    </span>
</React.Fragment>

const invokeRefInsert = ({quill, c}) => {
    const { APP } = c;
    const { URLContext } = APP;
    let index = (quill.getSelection() || {}).index;
    if (index === undefined || index < 0)
        index = quill.getLength();
    URLContext.actionHandler.runAction({
        action_full_name: URLContext.actionHandler.findUniqueAction("insert_reference").full_name,
        actorId: "about.About",
        response_callback: (data) => {
            if (data.success)
                quill.insertText(index, data.message);
        }
    });
}

const refInsert = ({quillRef, c}) => {
    if (!c.APP.state.site_data.installed_plugins.includes('memo'))
        return null;
    return <span className="ql-formats">
        <button type='button'
            onClick={() => invokeRefInsert({quill: quillRef.current, c})}
            aria-label='Open link dialog'>
            <i className="pi pi-link"></i></button>
    </span>
}

const commonHeader = ({quillRef, c, i18n, u}) => {
    return <>
        {quillToolbarHeaderTemplate}
        {refInsert({quillRef, c})}
        {
        <span className="ql-formats">
            <button type="button"
                onClick={() => {
                    const ctx = c;
                    const title = i18n.t("rows x columns");
                    const rows_text = i18n.t("Rows");
                    const columns_text = i18n.t("Columns");
                    const ok = (data) => {
                        const rows = parseInt(data[rows_text]);
                        const cols = parseInt(data[columns_text]);
                        const rowsNaN = u.isNaN(rows);
                        if (rowsNaN || u.isNaN(cols)) {
                            ctx.APP.toast.show({
                                severity: "warn",
                                summary: i18n.t("Not a number '{{dir}}'",
                                    {dir: rowsNaN
                                        ? i18n.t("rows")
                                        : i18n.t("columns")}),
                            });
                            return false;
                        }
                        const t = quillRef.current.getModule("table");
                        quillRef.current.focus();
                        t.insertTable(rows, cols);
                        return true;
                    }
                    ctx.APP.dialogFactory.createParamDialog(ctx, {
                        [rows_text]: {
                            react_name: "IntegerFieldElement",
                            default: 3,
                        },
                        [columns_text]: {
                            react_name: "IntegerFieldElement",
                            default: 3,
                        }
                    }, title, ok);
                }}>
                <i className="pi pi-table"></i></button>
        </span>
        }
        <span className="ql-formats">
            <button type="button"
                onClick={() => {
                    const quill = quillRef.current;
                    quill.focus();
                    const range = quill.getSelection();
                    const index = range ? range.index : quill.getLength();

                    const textbox_id = textboxId();
                    
                    // Insert a newline with textbox format to create the container
                    // This creates a TextBoxBlot container with a TextBoxBlock child
                    const delta = new Delta()
                        .retain(index)
                        .insert('\n', { 
                            'textbox': {
                                width: '50%',
                                align: '',
                            },
                            'textbox-block': textbox_id,
                        });
                    
                    quill.updateContents(delta, Quill.sources.USER);
                    
                    // Position cursor inside the textbox (at the beginning of the first block)
                    setTimeout(() => {
                        quill.setSelection(index, 0, Quill.sources.USER);
                    }, 0);
                }}
                title={i18n.t("Insert text box")}>
                <i className="pi pi-box"></i></button>
        </span>
    </>
}

export type QuillEditorProps = {
    autoFocus?: boolean;
    c: t.NavigationContext;
    headerExtend?: React.ReactNode;
    htmlValue?: string;
    inGrid: boolean;
    parent: t.LeafComponentInput & {quill?: Quill; props?: any;};
    plain: boolean;
    showHeader: boolean;
    value?: string;
};


export function QuillEditor(props: QuillEditorProps) {
    const quillRef = React.useRef<Quill | null>(null);
    const ctxMenuRef = React.useRef(null);
    const aControllerRef = React.useRef<AbortController | null>(null);
    const localEx = getExReady(
        exModulePromises,
        ["i18n", "prContextMenu", "u", "AbortController", "prUtils"],
        (mods) => {
            mods.i18n = mods.i18n.default;
            mods.AbortController = mods.AbortController.default;
            aControllerRef.current = new mods.AbortController();
            const { modules, meta } = getQuillModules({
                props,
                signal: aControllerRef.current.signal,
                i18n: mods.i18n,
                quillRef,
            });
            mods.modules = modules;
            mods.meta = meta;
            if (!props.showHeader) {
                mods.modules.toolbar = false;
            }
        }
    );
    React.useEffect(() => {
        return () => {
            if (aControllerRef.current) {
                aControllerRef.current.abort();
            }
        }
    }, []);
    return !localEx.ready ? null : <div
        onContextMenu={onRightClick({
            plain: props.plain,
            quillRef,
            elementRef: ctxMenuRef
        })}
        // onFocus={() => {
        //     const quill = quillRef.current;
        //     quill.setSelection(0, quill.getLength(), Quill.sources.USER);
        // }}
        onKeyDown={(e) => {
            if (e.ctrlKey && e.shiftKey && e.code == "KeyL") {
                e.stopPropagation();
                e.preventDefault();
                invokeRefInsert({quill: quillRef.current, c: props.c});
            }
        }}>
        {props.showHeader &&
            <div id={localEx.meta.toolbarID}>
                {props.plain ? refInsert({quillRef, c: props.c})
                    : commonHeader({quillRef, c: props.c, i18n: localEx.i18n, u: localEx.u})}
                {props.headerExtend}
            </div>
        }
        <QuillNextEditor 
            config={{modules: localEx.modules, theme: 'snow'}}
            defaultValue={props.plain ? new Delta().insert(props.value) : null}
            dangerouslySetInnerHTML={props.plain ? null : {__html: props.htmlValue}}
            onReady={(quill) => {
                quillRef.current = quill;
                props.parent.quill = quill;
                constants.debugMessage(
                    "Quill editor on",
                    props.parent.props.elem.name,
                    "autoFocus",
                    props.autoFocus,
                    "leafindex match",
                    props.parent.leafIndexMatch()
                );
                if (props.autoFocus) {
                    quill.focus();
                    let delta;
                    if (props.plain) {
                        delta = new Delta().insert(props.value || '');
                    } else {
                        delta = quill.clipboard.convert({ html: props.htmlValue || '' });
                    }
                    if (delta.length() === 0) {
                        setTimeout(() => {
                            quill.setSelection(0, 0, Quill.sources.USER);
                        }, 50);
                    }
                }

                if (!props.showHeader || props.inGrid || props.plain) return;
                if (props.c.APP.state.site_data.installed_plugins.includes('uploads')) {
                    overrideImageButtonHandler(quillRef);
                }
            }}
            onTextChange={changeDelta({
                parent: props.parent,
                plain: props.plain,
                prUtils: localEx.prUtils,
                quillRef,
            })}/>
        <localEx.prContextMenu.ContextMenu
            {...tableContextMenuProps({i18n: localEx.i18n, quillRef, c: props.c})}
            ref={ctxMenuRef}/>
        <div id="raw-editor-container"
            onKeyDown={e => e.stopPropagation()}></div>
    </div>
}
QuillEditor.propTypes = {
    value: (props, ...args: t.PropValidateRestArgs) => {
        if (props.plain) return PropTypes.string.isRequired(props, ...args);
        return null;
    },
    htmlValue: (props, ...args: t.PropValidateRestArgs) => {
        if (!props.plain) return PropTypes.string.isRequired(props, ...args);
        return null;
    },
    plain: PropTypes.bool.isRequired,
    showHeader: PropTypes.bool.isRequired,
    c: PropTypes.object.isRequired,
    parent: PropTypes.object.isRequired,
    inGrid: PropTypes.bool.isRequired,
    headerExtend: PropTypes.node,
    autoFocus: PropTypes.bool,
};
