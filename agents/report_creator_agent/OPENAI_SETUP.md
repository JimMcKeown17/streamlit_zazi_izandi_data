# OpenAI Integration Setup

## Prerequisites

1. **OpenAI API Key**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

2. **Environment Variables**: Create a `.env` file in your project root with:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. **Install Dependencies**: Run the following command to install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Analysis Methods

### 🔧 Tool-Enabled Analysis (Recommended)
Uses OpenAI function calling to dynamically explore your data:

**Capabilities:**
- 🎯 Dynamic data exploration and drill-downs
- 📊 Benchmark analysis with midline context  
- 🔍 Top/underperformer identification (schools, TAs, classes)
- 📈 Variance analysis across different groups
- 🚨 At-risk student identification
- 🔄 Interactive Q&A with follow-up questions
- 📱 Custom group comparisons
- 🎨 Visualization data preparation

**Files:**
- `ai_tools.py` - All analysis tools and functions
- `openai_tools_analysis.py` - OpenAI integration with function calling

### 📄 Context-Only Analysis  
Sends pre-calculated summaries to AI (original method):

**Capabilities:**
- Fast processing with pre-calculated statistics
- Standard benchmark comparisons
- Fixed analysis types (General/School/Grade)
- Good for simple overviews

**Files:**
- `openai_analysis.py` - Original context-based analysis

## Tool-Enabled Analysis Features

### 🔍 Performance Analysis Tools
- **Top Performers**: Identify best performing schools, TAs, or classes
- **Underperformers**: Find groups needing additional support
- **Benchmark Analysis**: Compare against midline/year-end targets
- **At-Risk Students**: Identify students needing intervention

### 📊 Data Exploration Tools
- **Filtering**: Query by grade, school, TA, score range, class
- **Variance Analysis**: Examine performance spread within groups
- **Group Comparisons**: Compare any two subsets of data
- **Distribution Analysis**: Understand score distributions

### 📈 Advanced Analytics
- **Midline Context**: All analysis considers June 2025 timing
- **Progress Projections**: Realistic year-end performance estimates
- **Intervention Targeting**: Specific recommendations for improvement
- **Equity Analysis**: Identify performance gaps

## Usage

1. Navigate to the "2025 Results" page
2. Go to the "2025 Midline" tab
3. Scroll down to the "🤖 AI Data Analysis" section
4. Choose your analysis method:
   - **Tool-Enabled (Recommended)**: For deep, interactive analysis
   - **Context-Only**: For quick standard analysis
5. Select your AI model and add custom questions (optional)
6. Click "🚀 Generate AI Analysis"

## Models Available

- **gpt-4o-mini**: Faster and more cost-effective, good for most analyses
- **gpt-4o**: More capable and detailed analysis, higher cost
- **gpt-3.5-turbo**: Fast and economical, basic analysis

## Example Questions for Tool-Enabled Analysis

### Performance Questions
- "Which schools are performing best and why?"
- "What TAs need additional support?"
- "How do our Grade 1 students compare to national averages?"

### Diagnostic Questions  
- "Which schools have the highest variance in performance?"
- "What percentage of students are at risk in each grade?"
- "How do different classes within the same school compare?"

### Strategic Questions
- "Based on midline progress, which schools will likely meet year-end targets?"
- "What interventions should we prioritize for the remaining months?"
- "Which TAs are most effective and could mentor others?"

## Data Privacy & Structure

- **Privacy**: No individual student data sent to OpenAI
- **Aggregation**: AI receives group statistics and summaries only
- **Security**: All analysis happens through controlled function calls
- **Transparency**: You can see exactly what data is analyzed

## Troubleshooting

- **API Key Error**: Ensure your `.env` file is in the project root and contains the correct API key
- **Import Error**: Make sure all Python files (`ai_tools.py`, `openai_tools_analysis.py`) are in your project directory
- **Tool Errors**: Check that your data has the expected column names (`letters_correct`, `grade_label`, etc.)
- **Connection Issues**: Check your internet connection and OpenAI service status

## File Structure

```
your_project/
├── .env                           # Your API key
├── ai_tools.py                    # Analysis tools (NEW)
├── openai_tools_analysis.py       # Tool-enabled analysis (NEW)
├── openai_analysis.py             # Context-only analysis (ORIGINAL)
├── pages_nav/page_2025_midline.py # Updated UI
└── requirements.txt               # Updated dependencies
```
