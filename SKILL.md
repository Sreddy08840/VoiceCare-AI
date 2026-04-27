# Skill: Appointment Booking

## Trigger
When user wants to book, reschedule, or cancel appointment

## Steps
1. Identify intent (book / reschedule / cancel)
2. Extract or ask for:
   - patient name
   - doctor/specialization
   - date
   - time
3. Validate input
4. Check availability (calendar API)
5. Handle conflicts:
   - Suggest alternative slots
6. Confirm details with user
7. Save appointment to database
8. Trigger notification

---

# Skill: Memory Manager

## Trigger
- At session start -> recall memory
- During conversation -> store important info
- At session end -> summarize

## Behavior
- Store:
  - preferred doctor
  - preferred time
  - past appointments

- Retrieve:
  - personalize responses
  - reduce repeated questions

---

# Skill: Error Handling

## Cases

1. Unclear input
-> "Sorry, I didn't understand. Could you repeat?"

2. Missing info
-> Ask specific question

3. Conflict
-> Suggest alternatives

4. Out-of-scope
-> "I can help only with medical appointments"

5. Change of mind
-> Confirm before updating
