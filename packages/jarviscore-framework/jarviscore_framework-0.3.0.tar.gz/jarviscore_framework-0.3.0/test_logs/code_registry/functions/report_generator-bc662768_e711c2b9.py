async def main():
    try:
        # Create invoice header with company name and date
        company_name = "Acme Corp"
        date = "Jan 2024"
        
        # Create formatted header
        width = 50
        border = "=" * width
        
        header_lines = [
            border,
            "",
            company_name.center(width),
            "",
            "INVOICE".center(width),
            "",
            f"Date: {date}".center(width),
            "",
            border
        ]
        
        report = "\n".join(header_lines)
        
        result = {
            'report': report
        }
        
        return result
        
    except Exception as e:
        result = {
            'report': f"Error generating invoice header: {str(e)}"
        }
        return result