import difflib

def generate_local_report(filename, original_code, upgraded_code):
    """
    Generates a 'Lovable-style' visual report that stays on the local disk.
    """
    diff = difflib.HtmlDiff().make_file(
        original_code.splitlines(), 
        upgraded_code.splitlines(), 
        fromdesc="Classical (Vulnerable)", 
        todesc="Post-Quantum (Safe)"
    )
    
    report_name = f"pqc_report_{filename}.html"
    with open(report_name, "w") as f:
        f.write(diff)
    
    return report_name