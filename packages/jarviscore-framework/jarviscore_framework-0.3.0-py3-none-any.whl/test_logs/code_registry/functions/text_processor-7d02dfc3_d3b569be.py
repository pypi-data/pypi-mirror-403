async def main():
    try:
        # Input product list
        product_string = "Widget=$10, Gadget=$25, Tool=$15"
        
        # Parse the product list
        products = product_string.split(", ")
        
        # Format as bulleted list
        bulleted_lines = []
        for product in products:
            # Split by = to get name and price
            parts = product.split("=")
            if len(parts) == 2:
                name = parts[0].strip()
                price = parts[1].strip()
                bulleted_lines.append(f"• {name}: {price}")
        
        # Join into final bulleted text
        bulleted_text = "\n".join(bulleted_lines)
        
        result = {
            "original": product_string,
            "bulleted_list": bulleted_text,
            "item_count": len(bulleted_lines),
            "items": [{"name": p.split("=")[0].strip(), "price": p.split("=")[1].strip()} for p in products]
        }
        
        return result
        
    except Exception as e:
        result = {
            "error": str(e),
            "bulleted_list": "",
            "item_count": 0
        }
        return result