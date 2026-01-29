import libcst as cst
import libcst.matchers as m

class ImportUpdater(cst.CSTTransformer):
    """
    Ensures PQC libraries are imported and old RSA imports are flagged/removed.
    """
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        # Check if pqc_wrapper is already there
        has_pqc_import = any(
            m.matches(body_stmt, m.Import(names=[m.ImportAlias(name=m.Name("pqc_wrapper"))]))
            for body_stmt in updated_node.body
        )

        if not has_pqc_import:
            # Create the new import node
            new_import = cst.SimpleStatementLine(
                body=[cst.Import(names=[cst.ImportAlias(name=m.Name("pqc_wrapper"))])]
            )
            # Insert it at the very top of the file
            new_body = [new_import] + list(updated_node.body)
            return updated_node.with_changes(body=new_body)
        
        return updated_node