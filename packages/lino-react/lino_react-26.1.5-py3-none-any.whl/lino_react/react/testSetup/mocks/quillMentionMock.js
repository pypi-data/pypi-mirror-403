// Mock for quill-mention module
// Provides valid Quill Blot and Module classes for registration

// MentionBlot needs to extend Quill's Embed blot
class MockMentionBlot {
    static blotName = 'mention';
    static tagName = 'span';
    static className = 'mention';
    
    constructor(domNode) {
        this.domNode = domNode;
    }
    
    static create(value) {
        const node = document.createElement('span');
        node.className = 'mention';
        return node;
    }
    
    static formats(domNode) {
        return {};
    }
    
    static value(domNode) {
        return {};
    }
}

// Mention module for Quill
class MockMention {
    constructor(quill, options) {
        this.quill = quill;
        this.options = options;
    }
}

export const Mention = MockMention;
export const MentionBlot = MockMentionBlot;
