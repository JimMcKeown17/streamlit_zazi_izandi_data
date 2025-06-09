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

## Features

The AI analysis integration provides three types of analysis:

### 📊 General Overview
- Overall program performance assessment
- Key strengths and areas for improvement
- Comparison to South African benchmarks
- Actionable recommendations
- Pattern identification

### 🏫 School Performance Analysis
- School performance variation analysis
- High-performing school identification
- Support recommendations for underperforming schools
- Equity and access insights
- Peer learning opportunities

### 📈 Grade Analysis
- Grade-specific performance analysis
- Grade R vs Grade 1 comparison
- Age-appropriate progress assessment
- Grade-specific intervention recommendations
- Next grade level readiness analysis

## Usage

1. Navigate to the "2025 Results" page
2. Go to the "2025 Midline" tab
3. Scroll down to the "🤖 AI Data Analysis" section
4. Select your analysis type and AI model
5. Optionally add custom questions
6. Click "🚀 Generate AI Analysis"

## Models Available

- **gpt-4o-mini**: Faster and more cost-effective, good for most analyses
- **gpt-4o**: More capable and detailed analysis, higher cost
- **gpt-3.5-turbo**: Fast and economical, basic analysis

## Custom Questions

You can ask specific questions like:
- "What factors might explain school performance differences?"
- "How can we improve Grade R letter recognition?"
- "Which schools would benefit from additional TA support?"
- "What patterns do you see in student performance by class size?"

## Data Structure

The AI receives structured summaries of your data, not raw student information. This includes:
- Aggregate statistics
- School-level averages
- Grade-level performance
- Benchmark comparisons

## Troubleshooting

- **API Key Error**: Ensure your `.env` file is in the project root and contains the correct API key
- **Import Error**: Make sure `openai_analysis.py` is in your project directory
- **Connection Issues**: Check your internet connection and OpenAI service status 