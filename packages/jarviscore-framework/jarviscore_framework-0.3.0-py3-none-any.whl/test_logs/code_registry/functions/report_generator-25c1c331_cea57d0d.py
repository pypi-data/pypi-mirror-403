async def main():
    try:
        # Create invoice header with company name and date
        company_name = "Acme Corp"
        date = "Jan 2024"
        
        # Create formatted header
        header_width = 50
        border = "=" * header_width
        
        # Center the company name and date
        company_line = company_name.center(header_width)
        date_line = date.center(header_width)
        title_line = "INVOICE".center(header_width)
        
        # Build the invoice header
        invoice_header = f"""
{border}
{company_line}
{title_line}
{date_line}
{border}
"""
        
        result = {
            'report': invoice_header.strip()
        }
        
        return result
        
    except Exception as e:
        result = {
            'report': f"Error generating invoice header: {str(e)}"
        }
        return result