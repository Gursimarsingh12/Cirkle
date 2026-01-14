#!/usr/bin/env python3
"""
Full test runner for the new recommendation system.
This script will:
1. Generate mock data with the right user distribution
2. Test the recommendation system with different page sizes
3. Validate the percentage-based priority distribution
"""

import sys
import os
import asyncio
import subprocess

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)


async def run_mock_data_generation():
    """Run the mock data generation script"""
    print("🚀 STEP 1: GENERATING MOCK DATA")
    print("=" * 60)
    
    try:
        # Run the mock data generation script
        result = subprocess.run([
            sys.executable, 
            os.path.join(current_dir, "generate_mock_data.py")
        ], capture_output=True, text=True, cwd=src_dir)
        
        if result.returncode == 0:
            print("✅ Mock data generation completed successfully!")
            print("\n📊 MOCK DATA SUMMARY:")
            # Print the last few lines of output which contain the summary
            output_lines = result.stdout.split('\n')
            summary_started = False
            for line in output_lines:
                if "Enhanced User Creation Summary" in line or summary_started:
                    summary_started = True
                    print(line)
                elif "✅ Enhanced mock data generation completed successfully!" in line:
                    print(line)
                    break
            return True
        else:
            print("❌ Mock data generation failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running mock data generation: {str(e)}")
        return False


async def run_recommendation_test():
    """Run the recommendation system test"""
    print("\n🎯 STEP 2: TESTING RECOMMENDATION SYSTEM")
    print("=" * 60)
    
    try:
        # Import and run the test
        from test_recommendation_system import main as test_main
        await test_main()
        return True
        
    except Exception as e:
        print(f"❌ Error running recommendation test: {str(e)}")
        return False


async def main():
    """Main function to run the complete test suite"""
    print("🔥 COMPREHENSIVE RECOMMENDATION SYSTEM TEST")
    print("=" * 80)
    print("This will generate fresh mock data and test the new recommendation system")
    print("=" * 80)
    
    # Step 1: Generate mock data
    mock_data_success = await run_mock_data_generation()
    
    if not mock_data_success:
        print("❌ Cannot proceed with testing due to mock data generation failure")
        return
    
    # Step 2: Test recommendation system
    test_success = await run_recommendation_test()
    
    if test_success:
        print("\n🎉 COMPLETE TEST SUITE PASSED!")
        print("=" * 80)
        print("✅ Mock data generated successfully")
        print("✅ Recommendation system working correctly")
        print("✅ Percentage-based distribution validated")
        print("🚀 Your new Twitter-like recommendation system is ready!")
        print("=" * 80)
    else:
        print("\n❌ TEST SUITE FAILED!")
        print("Please check the errors above and fix any issues.")


if __name__ == "__main__":
    asyncio.run(main()) 