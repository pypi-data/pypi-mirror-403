async def main():
    try:
        # Get data from previous step if available, otherwise use provided defaults
        previous_data = {'name': 'John', 'age': 30, 'city': 'NYC'}
        
        # Check if we have previous step results
        try:
            if 'step0' in globals().get('previous_step_results', {}):
                previous_data = previous_step_results['step0']
        except:
            pass
        
        # Extract person data
        name = previous_data.get('name', 'John')
        age = previous_data.get('age', 30)
        city = previous_data.get('city', 'NYC')
        
        # Create formatted text report
        report_lines = [
            "=" * 40,
            "PERSON INFORMATION REPORT",
            "=" * 40,
            "",
            f"Name:     {name}",
            f"Age:      {age}",
            f"City:     {city}",
            "",
            "-" * 40,
            f"Summary: {name} is {age} years old and lives in {city}.",
            "-" * 40,
            "",
            "Report generated successfully.",
            "=" * 40
        ]
        
        report = "\n".join(report_lines)
        
        result = {
            'report': report
        }
        
        return result
        
    except Exception as e:
        return {
            'report': f"Error generating report: {str(e)}"
        }