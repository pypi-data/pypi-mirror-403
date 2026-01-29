import libcst as cst

class PQCTransformer(cst.CSTTransformer):
    """
    The engine that finds RSA logic and swaps it for ML-KEM (Kyber).
    """
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        # 1. Identify if the function being called is RSA generation
        if m.matches(updated_node, m.Call(func=m.Attribute(attr=m.Name("generate_private_key")))):
            
            # 2. Rewrite the call to use our Post-Quantum Library
            return updated_node.with_changes(
                func=cst.Attribute(
                    value=cst.Name("pqc_wrapper"),
                    attr=cst.Name("ml_kem_generate")
                ),
                # 3. Inject the correct PQC parameters (e.g., ML-KEM-768)
                args=[cst.Arg(value=cst.SimpleString("'ML-KEM-768'"))]
            )
        return updated_node

# Implementation Logic
source_code = """
from cryptography.hazmat.primitives.asymmetric import rsa
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
"""

tree = cst.parse_module(source_code)
wrapper = cst.MetadataWrapper(tree)
transformer = PQCTransformer()
new_tree = wrapper.visit(transformer)

print(new_tree.code)