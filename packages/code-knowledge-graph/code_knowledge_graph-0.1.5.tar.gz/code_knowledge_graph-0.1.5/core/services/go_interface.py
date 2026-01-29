"""Go Interface Implementation Detection Service.

This module implements Go interface implementation detection using method set
fingerprinting. Go uses duck typing for interfaces (implicit implementation),
so we need to match structs to interfaces by comparing their method sets.

Feature: code-knowledge-graph-enhancement
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


@dataclass
class InterfaceImplementation:
    """Represents an interface implementation relationship.
    
    In Go, a struct implicitly implements an interface if it has all the
    methods defined by the interface. This class captures that relationship.
    
    Attributes:
        interface_name: Name of the interface
        interface_file: File path where the interface is defined
        struct_name: Name of the struct that implements the interface
        struct_file: File path where the struct is defined
        confidence: Match confidence (0-1), based on method set overlap
    """
    interface_name: str
    interface_file: str
    struct_name: str
    struct_file: str
    confidence: float  # 0-1, based on method set overlap


class GoInterfaceResolver:
    """Go interface implementation resolver.
    
    Detects which structs implement which interfaces using method set
    fingerprinting. In Go, interfaces are implemented implicitly - a struct
    implements an interface if it has all the methods defined by the interface.
    
    Method Set Fingerprint Format:
        Sorted method signatures joined by "|"
        Example: "Close():error|Read([]byte):(int,error)|Write([]byte):(int,error)"
    
    The fingerprint is stored in the `method_set_signature` column of the
    symbols table for structs, enabling efficient interface matching.
    """
    
    def __init__(self, storage: SQLiteStorage):
        """Initialize Go interface resolver.
        
        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage
    
    def find_implementations(
        self,
        project_id: int,
        interface_name: str
    ) -> list[InterfaceImplementation]:
        """Find all structs that implement a given interface.
        
        Searches for structs whose method set contains all methods defined
        by the interface. Uses method set fingerprinting for efficient matching.
        
        Args:
            project_id: Project ID
            interface_name: Name of the interface to find implementations for
            
        Returns:
            List of InterfaceImplementation objects representing structs
            that implement the interface
        """
        # 1. Get interface methods
        interface_methods = self._get_interface_methods(project_id, interface_name)
        if not interface_methods:
            logger.debug(f"No methods found for interface: {interface_name}")
            return []
        
        # 2. Compute interface method fingerprint
        interface_fingerprint = self._compute_method_fingerprint(interface_methods)
        if not interface_fingerprint:
            return []
        
        # 3. Get interface file path for result
        interface_file = self._get_interface_file(project_id, interface_name)
        
        # 4. Find matching structs
        return self._find_matching_structs(
            project_id, 
            interface_name, 
            interface_file,
            interface_fingerprint
        )
    
    def find_interfaces_for_struct(
        self,
        project_id: int,
        struct_name: str
    ) -> list[InterfaceImplementation]:
        """Find all interfaces that a struct implements.
        
        Searches for interfaces whose method set is a subset of the struct's
        method set.
        
        Args:
            project_id: Project ID
            struct_name: Name of the struct
            
        Returns:
            List of InterfaceImplementation objects representing interfaces
            that the struct implements
        """
        # 1. Get struct methods
        struct_methods = self._get_struct_methods(project_id, struct_name)
        if not struct_methods:
            logger.debug(f"No methods found for struct: {struct_name}")
            return []
        
        # 2. Compute struct method fingerprint
        struct_fingerprint = self._compute_method_fingerprint(struct_methods)
        if not struct_fingerprint:
            return []
        
        struct_method_set = set(struct_fingerprint.split("|"))
        
        # 3. Get struct file path for result
        struct_file = self._get_struct_file(project_id, struct_name)
        
        # 4. Find all interfaces and check if struct implements them
        results = []
        interfaces = self._get_all_interfaces(project_id)
        
        for interface in interfaces:
            interface_methods = self._get_interface_methods(
                project_id, interface["name"]
            )
            if not interface_methods:
                continue
            
            interface_fingerprint = self._compute_method_fingerprint(interface_methods)
            if not interface_fingerprint:
                continue
            
            interface_method_set = set(interface_fingerprint.split("|"))
            
            # Check if struct implements all interface methods
            if interface_method_set.issubset(struct_method_set):
                # Calculate confidence based on method set overlap
                confidence = len(interface_method_set) / len(struct_method_set)
                
                results.append(InterfaceImplementation(
                    interface_name=interface["name"],
                    interface_file=interface["file_path"],
                    struct_name=struct_name,
                    struct_file=struct_file,
                    confidence=confidence
                ))
        
        return results
    
    def update_struct_method_fingerprint(
        self,
        project_id: int,
        struct_name: str
    ) -> Optional[str]:
        """Update the method set fingerprint for a struct.
        
        Computes and stores the method set fingerprint for a struct in the
        symbols table. This should be called during the parsing phase for
        each struct.
        
        Args:
            project_id: Project ID
            struct_name: Name of the struct
            
        Returns:
            The computed fingerprint, or None if no methods found
        """
        # Get struct methods
        methods = self._get_struct_methods(project_id, struct_name)
        if not methods:
            return None
        
        # Compute fingerprint
        fingerprint = self._compute_method_fingerprint(methods)
        if not fingerprint:
            return None
        
        # Update in database
        cursor = self.storage._get_cursor()
        cursor.execute("""
            UPDATE symbols 
            SET method_set_signature = ?
            WHERE file_id IN (SELECT id FROM files WHERE project_id = ?)
              AND symbol_type = 'struct'
              AND name = ?
        """, (fingerprint, project_id, struct_name))
        self.storage.conn.commit()
        
        logger.debug(f"Updated method fingerprint for struct {struct_name}: {fingerprint}")
        return fingerprint
    
    def _compute_method_fingerprint(self, methods: list[dict]) -> str:
        """Compute method set fingerprint from a list of methods.
        
        Creates a canonical fingerprint by normalizing and sorting method
        signatures, then joining them with "|".
        
        Args:
            methods: List of method dicts with "name" and "signature" keys
            
        Returns:
            Fingerprint string, e.g., "Close():error|Read([]byte):(int,error)"
        """
        if not methods:
            return ""
        
        signatures = []
        for method in methods:
            name = method.get("name", "")
            signature = method.get("signature", "")
            
            # Normalize the signature
            normalized = self._normalize_signature(name, signature)
            if normalized:
                signatures.append(normalized)
        
        # Sort for canonical ordering
        signatures.sort()
        
        return "|".join(signatures)
    
    def _normalize_signature(self, name: str, signature: str) -> str:
        """Normalize a method signature for fingerprinting.
        
        Removes the receiver from Go method signatures and standardizes
        the format to: MethodName(params):returns
        
        Examples:
            Input:  "func (s *Server) Start(ctx context.Context) error"
            Output: "Start(context.Context):error"
            
            Input:  "func (r *Reader) Read(p []byte) (n int, err error)"
            Output: "Read([]byte):(int,error)"
        
        Args:
            name: Method name
            signature: Full method signature
            
        Returns:
            Normalized signature string
        """
        if not name:
            return ""
        
        # If signature is empty or just the name, return name with empty params
        if not signature or signature == name:
            return f"{name}()"
        
        # Try to parse Go function signature
        # Pattern: func (receiver) Name(params) returns
        # or: func Name(params) returns
        
        # Remove "func " prefix if present
        sig = signature.strip()
        if sig.startswith("func "):
            sig = sig[5:].strip()
        
        # Remove receiver if present: (s *Server) or (s Server)
        receiver_pattern = r'^\([^)]+\)\s*'
        sig = re.sub(receiver_pattern, '', sig)
        
        # Now we should have: Name(params) returns or Name(params)
        # Extract method name, params, and return type
        
        # Find the method name and parameters
        match = re.match(r'(\w+)\s*\(([^)]*)\)\s*(.*)', sig)
        if not match:
            # Fallback: just use the name
            return f"{name}()"
        
        method_name = match.group(1)
        params_str = match.group(2).strip()
        returns_str = match.group(3).strip()
        
        # Normalize parameters: remove names, keep only types
        normalized_params = self._normalize_params(params_str)
        
        # Normalize return type
        normalized_returns = self._normalize_returns(returns_str)
        
        # Build normalized signature
        result = f"{method_name}({normalized_params})"
        if normalized_returns:
            result += f":{normalized_returns}"
        
        return result
    
    def _normalize_params(self, params_str: str) -> str:
        """Normalize parameter list to types only.
        
        Removes parameter names, keeping only types.
        
        Examples:
            "ctx context.Context, name string" -> "context.Context,string"
            "p []byte" -> "[]byte"
            "" -> ""
        
        Args:
            params_str: Parameter string from signature
            
        Returns:
            Normalized parameter types
        """
        if not params_str:
            return ""
        
        # Split by comma
        params = [p.strip() for p in params_str.split(",")]
        types = []
        
        for param in params:
            if not param:
                continue
            
            # Parameter format: "name type" or just "type"
            # Handle variadic: "args ...string"
            parts = param.split()
            
            if len(parts) >= 2:
                # Has name and type
                param_type = " ".join(parts[1:])
            else:
                # Just type (or name with implicit type from previous)
                param_type = parts[0]
            
            # Clean up the type
            param_type = param_type.strip()
            if param_type:
                types.append(param_type)
        
        return ",".join(types)
    
    def _normalize_returns(self, returns_str: str) -> str:
        """Normalize return type string.
        
        Handles single returns, multiple returns in parentheses, and named returns.
        
        Examples:
            "error" -> "error"
            "(int, error)" -> "(int,error)"
            "(n int, err error)" -> "(int,error)"
            "" -> ""
        
        Args:
            returns_str: Return type string from signature
            
        Returns:
            Normalized return type
        """
        if not returns_str:
            return ""
        
        returns_str = returns_str.strip()
        
        # Check if it's a tuple return: (type1, type2) or (name type1, name type2)
        if returns_str.startswith("(") and returns_str.endswith(")"):
            inner = returns_str[1:-1].strip()
            
            # Split by comma and normalize each
            parts = [p.strip() for p in inner.split(",")]
            types = []
            
            for part in parts:
                if not part:
                    continue
                
                # Could be "name type" or just "type"
                tokens = part.split()
                if len(tokens) >= 2:
                    # Named return: take the type (last token)
                    types.append(tokens[-1])
                else:
                    types.append(tokens[0])
            
            if len(types) == 1:
                return types[0]
            return f"({','.join(types)})"
        
        # Single return type (might have a name)
        parts = returns_str.split()
        if len(parts) >= 2:
            # Named return
            return parts[-1]
        return returns_str
    
    def _get_interface_methods(
        self,
        project_id: int,
        interface_name: str
    ) -> list[dict]:
        """Get all methods defined by an interface.
        
        Args:
            project_id: Project ID
            interface_name: Interface name
            
        Returns:
            List of method dicts with "name" and "signature" keys
        """
        cursor = self.storage._get_cursor()
        cursor.execute("""
            SELECT s.name, s.signature
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.symbol_type = 'method'
              AND s.container_name = ?
        """, (project_id, interface_name))
        
        return [{"name": row[0], "signature": row[1]} for row in cursor.fetchall()]
    
    def _get_struct_methods(
        self,
        project_id: int,
        struct_name: str
    ) -> list[dict]:
        """Get all methods for a struct (including pointer receiver methods).
        
        Args:
            project_id: Project ID
            struct_name: Struct name
            
        Returns:
            List of method dicts with "name" and "signature" keys
        """
        cursor = self.storage._get_cursor()
        # Match both value receiver (StructName) and pointer receiver (*StructName)
        cursor.execute("""
            SELECT s.name, s.signature
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.symbol_type = 'method'
              AND (s.container_name = ? OR s.container_name = ?)
        """, (project_id, struct_name, f"*{struct_name}"))
        
        return [{"name": row[0], "signature": row[1]} for row in cursor.fetchall()]
    
    def _get_interface_file(
        self,
        project_id: int,
        interface_name: str
    ) -> str:
        """Get the file path where an interface is defined.
        
        Args:
            project_id: Project ID
            interface_name: Interface name
            
        Returns:
            Relative file path, or empty string if not found
        """
        cursor = self.storage._get_cursor()
        cursor.execute("""
            SELECT f.relative_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.symbol_type = 'interface'
              AND s.name = ?
            LIMIT 1
        """, (project_id, interface_name))
        
        row = cursor.fetchone()
        return row[0] if row else ""
    
    def _get_struct_file(
        self,
        project_id: int,
        struct_name: str
    ) -> str:
        """Get the file path where a struct is defined.
        
        Args:
            project_id: Project ID
            struct_name: Struct name
            
        Returns:
            Relative file path, or empty string if not found
        """
        cursor = self.storage._get_cursor()
        cursor.execute("""
            SELECT f.relative_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.symbol_type = 'struct'
              AND s.name = ?
            LIMIT 1
        """, (project_id, struct_name))
        
        row = cursor.fetchone()
        return row[0] if row else ""
    
    def _get_all_interfaces(self, project_id: int) -> list[dict]:
        """Get all interfaces in a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of interface dicts with "name" and "file_path" keys
        """
        cursor = self.storage._get_cursor()
        cursor.execute("""
            SELECT s.name, f.relative_path as file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.symbol_type = 'interface'
        """, (project_id,))
        
        return [{"name": row[0], "file_path": row[1]} for row in cursor.fetchall()]
    
    def _find_matching_structs(
        self,
        project_id: int,
        interface_name: str,
        interface_file: str,
        interface_fingerprint: str
    ) -> list[InterfaceImplementation]:
        """Find structs whose method set contains the interface's method set.
        
        Args:
            project_id: Project ID
            interface_name: Interface name
            interface_file: Interface file path
            interface_fingerprint: Interface method fingerprint
            
        Returns:
            List of InterfaceImplementation objects
        """
        cursor = self.storage._get_cursor()
        
        # Get all structs with method set signatures
        cursor.execute("""
            SELECT s.name, s.method_set_signature, f.relative_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.symbol_type = 'struct'
              AND s.method_set_signature IS NOT NULL
              AND s.method_set_signature != ''
        """, (project_id,))
        
        results = []
        interface_methods = set(interface_fingerprint.split("|"))
        
        for row in cursor.fetchall():
            struct_name = row[0]
            struct_fingerprint = row[1]
            struct_file = row[2]
            
            if not struct_fingerprint:
                continue
            
            struct_methods = set(struct_fingerprint.split("|"))
            
            # Check if struct's method set contains all interface methods
            if interface_methods.issubset(struct_methods):
                # Calculate confidence: ratio of interface methods to struct methods
                # Higher confidence means the struct is more specialized for this interface
                confidence = len(interface_methods) / len(struct_methods) if struct_methods else 0
                
                results.append(InterfaceImplementation(
                    interface_name=interface_name,
                    interface_file=interface_file,
                    struct_name=struct_name,
                    struct_file=struct_file,
                    confidence=confidence
                ))
        
        # Sort by confidence (higher first)
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        return results
    
    def get_potential_implementations_for_call(
        self,
        project_id: int,
        interface_name: str,
        method_name: str
    ) -> list[dict]:
        """Get potential implementation targets for an interface method call.
        
        Used by call chain tracing to find all possible implementations
        when tracing a call to an interface method.
        
        Args:
            project_id: Project ID
            interface_name: Interface name
            method_name: Method being called
            
        Returns:
            List of dicts with struct info for potential call targets
        """
        implementations = self.find_implementations(project_id, interface_name)
        
        results = []
        for impl in implementations:
            # Get the method symbol for this struct
            cursor = self.storage._get_cursor()
            cursor.execute("""
                SELECT s.id, s.name, s.signature, s.start_line, f.relative_path
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
                  AND s.symbol_type = 'method'
                  AND s.name = ?
                  AND (s.container_name = ? OR s.container_name = ?)
                LIMIT 1
            """, (project_id, method_name, impl.struct_name, f"*{impl.struct_name}"))
            
            row = cursor.fetchone()
            if row:
                results.append({
                    "symbol_id": row[0],
                    "method_name": row[1],
                    "signature": row[2],
                    "line_number": row[3],
                    "file_path": row[4],
                    "struct_name": impl.struct_name,
                    "confidence": impl.confidence,
                    "call_type": "potential"
                })
        
        return results
