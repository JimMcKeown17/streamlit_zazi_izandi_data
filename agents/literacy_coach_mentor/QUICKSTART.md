# Literacy Coach Mentor - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Check Prerequisites

Ensure you have:
- ✅ OpenAI API key set in `.env` file
- ✅ Database connection configured (`RENDER_DATABASE_URL` in `.env`)
- ✅ All dependencies installed (`pip install -r requirements.txt`)

### Step 2: Run the Application

```bash
streamlit run new_pages/coach_assistant.py
```

### Step 3: Login and Ask Questions

1. Enter your TeamPact User ID in the sidebar
2. Click "Login"
3. Start asking questions!

## 📝 Example Questions to Try

### Getting Started
```
"How am I doing overall?"
```
This gives you a comprehensive overview of your performance.

### Check Your Pacing
```
"Am I moving through letters at the right speed?"
```
Compares your pace to the expected 2 letters per 3 sessions.

### Check Differentiation
```
"Am I teaching my groups at the right levels?"
```
Analyzes whether your groups are appropriately differentiated.

### Compare to Benchmarks
```
"How do my learners compare to other schools?"
```
Shows how your groups perform against national and programme benchmarks.

## 🎯 What the AI Can Tell You

### ✅ Session Frequency
- How many sessions per week you're delivering
- Whether you're meeting the 3+ sessions/week target
- Gaps or inconsistencies in your schedule

### ✅ Pacing
- How fast you're moving through the letter sequence
- Whether pace is appropriate for your grade
- Suggestions for speeding up or slowing down

### ✅ Differentiation
- Whether different groups are at different levels
- If 3+ groups are stuck at the same position (red flag)
- Tips for better group formation

### ✅ Performance
- How your learners compare to Eastern Cape benchmarks
- Attendance rates and their impact
- Progress relative to programme targets

## 🔧 Troubleshooting

### "No data found for user_id"
**Solution**: Check that:
- Your user_id is correct (ask your mentor if unsure)
- You have recorded sessions in TeamPact
- Sessions include letters taught

### Agent not responding
**Solution**: Check:
- OpenAI API key is set correctly in `.env`
- Database connection is working
- Console for error messages

### Slow responses
**Normal**: First query takes longer (10-30 seconds)
- Subsequent queries are faster
- Complex questions requiring multiple analyses take longer

## 📊 Understanding Your Results

### Session Frequency
- **Target**: 3+ sessions per week
- **Good**: Consistent schedule, few gaps
- **Needs Work**: <2 sessions/week, long gaps

### Pacing (Grade 1)
- **Target**: ~2 new letters every 3 sessions
- **Good**: Steady progress through sequence
- **Needs Work**: Stuck on same letters or moving too fast

### Differentiation
- **Good**: Different groups at different positions
- **Red Flag**: 3+ groups at exact same position
- **Best Practice**: Groups matched to children's current knowledge

### Attendance
- **Target**: >80%
- **Good**: Consistent attendance across groups
- **Needs Work**: <70% attendance

## 💡 Pro Tips

1. **Ask follow-up questions** - The AI remembers context within a conversation
2. **Be specific** - "How is Group 1A doing?" gets more detailed feedback
3. **Ask for suggestions** - "What should I focus on this week?"
4. **Check regularly** - Weekly check-ins help track progress
5. **Use quick buttons** - Faster than typing common questions

## 📱 For Mobile Users

The Streamlit interface works on mobile browsers:
1. Open your browser
2. Navigate to the app URL
3. Login with your user_id
4. Use voice-to-text for questions (if available)

## 🆘 Need Help?

1. **Check the USAGE.md** for detailed examples
2. **Review README.md** for technical details
3. **Contact your mentor** for programme-specific questions
4. **Check error messages** in the app for debugging hints

## 🎓 Learning Resources

### Letter Sequence (Memorize This!)
```
a, e, i, o, u, b, l, m, k, p, s, h, z, n, d, y, f, w, v, x, g, t, q, r, c, j
```

### Key Benchmarks
- **Eastern Cape**: Only 27% of Grade 1 learners reach 40 letters/minute
- **National**: <50% know all letters by end of Grade 1
- **Zazi iZandi**: 53-74% reaching benchmarks (you're making a difference!)

### Programme Targets
- ✅ 3+ sessions per week
- ✅ 2 letters per 3 sessions (Grade 1)
- ✅ >80% attendance
- ✅ Differentiated groups

## 🌟 Remember

You're making a real difference in children's lives! The AI is here to support you, not judge you. Every coaching session helps children learn to read, which changes their future.

Keep up the great work! 🎉

