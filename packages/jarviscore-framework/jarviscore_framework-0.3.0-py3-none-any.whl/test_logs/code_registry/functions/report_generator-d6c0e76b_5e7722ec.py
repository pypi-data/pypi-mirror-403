async def main():
    try:
        # Get data from previous step if available, otherwise use provided data
        previous_data = {'name': 'John', 'age': 30, 'city': 'NYC'}
        
        # Check if we have previous step results
        try:
            if 'step0' in previous_step_results:
                previous_data = previous_step_results['step0']
        except NameError:
            pass
        
        name = previous_data.get('name', 'John')
        age = previous_data.get('age', 30)
        city = previous_data.get('city', 'NYC')
        
        # Create formatted text report
        report_lines = [
            "=" * 40,
            "PERSON INFORMATION REPORT",
            "=" * 40,
            "",
            f"{'Name:':<15} {name}",
            f"{'Age:':<15} {age}",
            f"{'City:':<15} {city}",
            "",
            "-" * 40,
            f"Report generated successfully",
            "=" * 40
        ]
        
        report = "\n".join(report_lines)
        
        result = {
            'report': report
        }
        
        return result
        
    except Exception as e:
        result = {
            'report': f"Error generating report: {str(e)}"
        }
        return result