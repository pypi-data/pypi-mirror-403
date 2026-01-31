def main():
    # Input product list
    product_string = "Widget=$10, Gadget=$25, Tool=$15"
    
    try:
        # Split the string by comma and strip whitespace
        products = [item.strip() for item in product_string.split(",")]
        
        # Create bulleted list
        bulleted_items = []
        for product in products:
            # Split by = to get name and price
            parts = product.split("=")
            if len(parts) == 2:
                name = parts[0].strip()
                price = parts[1].strip()
                bulleted_items.append(f"• {name}: {price}")
            else:
                bulleted_items.append(f"• {product}")
        
        # Join into final bulleted text
        bulleted_text = "\n".join(bulleted_items)
        
        result = {
            "original": product_string,
            "bulleted_list": bulleted_text,
            "item_count": len(bulleted_items),
            "items": bulleted_items
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "original": product_string,
            "bulleted_list": "",
            "item_count": 0,
            "items": []
        }

result = main()