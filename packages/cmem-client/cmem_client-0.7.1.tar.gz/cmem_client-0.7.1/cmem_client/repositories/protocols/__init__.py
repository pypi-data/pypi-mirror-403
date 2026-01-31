"""Protocol interfaces for repository operations.

This package defines protocol interfaces that repositories can implement to
provide consistent operations. Protocols
allow for type-safe composition of repository functionality without requiring
inheritance from concrete base classes.

Available protocols:
- CreateItemProtocol: For repositories that can create new items
- DeleteItemProtocol: For repositories that can delete existing items
- ImportItemProtocol: For repositories that can import items from files

Repositories mix and match these protocols based on their capabilities,
ensuring consistent interfaces across different resource types.
"""
