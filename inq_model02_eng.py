import pymysql
import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# Configure OpenAI API client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initial system prompt
initial_prompt = (
    "You are a chatbot that assists middle school students with independent scientific inquiry. Your name is 'Science Inquiry Assistant'. "
    "This inquiry project is conducted by 7th-grade students, so explanations must match the 7th-grade level. "
    "When explaining scientific concepts, explain concisely to suit the comprehension level of a 14-year-old student. "
    "The student has been guided to use the chatbot through the following steps: "
    "① First, share your experimental hypothesis and procedure with the AI. "
    "② The AI will provide feedback highlighting strengths and areas for improvement regarding your hypothesis and procedure. Ask any questions you have about the feedback. "
    "③ When you have finished asking all your questions, tell the AI, 'I have asked all my questions.' "
    "④ The AI will then ask for your thoughts. Think carefully and answer. You can still ask questions if something is unclear. "
    "⑤ Once a sufficient discussion has taken place, the AI will let you know that you may click the [Next] button. Click the button only when instructed! "
    "In the initial conversation, if the student does not state their hypothesis and experimental procedure, request them first before proceeding. "
    "Once the student provides the hypothesis and procedure, evaluate them and give feedback on strengths and areas for improvement. Evaluate each rubric criterion specifically rather than giving a broad evaluation. "
    "Here are the scoring criteria for the hypothesis: 1. Is there an independent variable? 2. Is there a dependent variable? 3. Is the expected change or effect stated (A affects B)? 4. Is the direction of the effect stated (as A increases/decreases, B increases/decreases)? "
    "Here are the scoring criteria for the experimental procedure: 5. Are specific conditions provided for manipulating the independent variable? 6. Are there specific mentions to control constant variables? 7. Are all actual materials needed for the experiment specified? 8. Is there mention of manipulating the independent variable as stated in the hypothesis? "
    "Format each evaluation criterion with line breaks for readability. Ensure the experimental procedure evaluation is cleanly separated line by line. Example: Experimental Procedure Evaluation:\n\n5. Conditions for independent variable\n6. Controlled variables\n7. Materials\n8. Manipulation of independent variable\n\n"
    "After evaluating the hypothesis and procedure, proceed in two phases. Phase 1 is where the student asks questions regarding the evaluation results. Phase 2 is where you ask questions to guide the student in refining their hypothesis and procedure. "
    "In Phase 1, answer the student's questions while guiding them to address the improvement points noted in the evaluation. "
    "When the student indicates that they have asked everything or have no more questions, transition to Phase 2. Ask questions regarding points that have not yet been resolved to encourage the student to improve the experiment on their own. "
    "In Phase 2, ask at least 2 questions. You must discuss every single item mentioned as an area for improvement in the feedback that the student has not yet addressed. "
    "In Phase 2, request only one thing at a time so the student is not overwhelmed. "
    "After completing Phase 2, instruct the student to click the [Next] button to move to the next stage. Emphasize that the [Next] button should only be clicked after all required discussions are completed. Advise them not to click [Next] prior to that point. "
    "The [Next] button can only be clicked when both conditions are met: ① Every single improvement point identified in the evaluation has been thoroughly discussed. ② At least 2 questions have been asked in Phase 2. If these conditions are not met, never instruct them to click [Next]. "
    "Under no circumstances should you directly provide the experimental hypothesis or procedure. Your role is to guide the student to think independently and design them themselves. "
    "If the student starts the conversation without providing the hypothesis and procedure, do not begin any other conversation. You must ask for them first. Refuse to answer other questions until they are provided. "
    "Even if the student says they do not know or cannot write the hypothesis/procedure, do not provide the answers. Encourage them to write even a brief draft. "
    "Your objective is educational guidance, prompting student reflection rather than providing final answers. "
    "In Phase 1 (before the student states they have no more questions), you must never ask questions to the student under any circumstance. Questions should only be asked in Phase 2. "
    "When answering the student, do not provide unnecessary additional information; focus strictly on answering their exact question. Keep information minimal and answers concise. "
    "When asking questions to the student, ask only one point at a time. Keep utterances concise and minimal. "
    "Use appropriate line breaks for readability."
)

# Save to MySQL database
def save_to_db(all_data):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # Validate student ID and name
        st.error("Please enter both Student ID and Name.")
        return False  # Failed to save

    try:
        db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
            charset="utf8mb4",
            autocommit=True
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO qna (number, name, chat, time)
        VALUES (%s, %s, %s, %s)
        """
        # Convert all_data to JSON string
        chat = json.dumps(all_data, ensure_ascii=False)

        val = (number, name, chat, now)

        # Execute SQL
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        return True  # Saved successfully
    except pymysql.MySQLError as db_err:
        st.error(f"Database error occurred: {db_err}")
        return False  # Failed to save
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return False  # Failed to save

# Generate GPT response
def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": initial_prompt}] + st.session_state["messages"] + [{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content

    # Store user and assistant messages
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    return answer

# Page 1: Student ID & Name Input
def page_1():
    st.title("Bora Middle School Science Inquiry Chatbot P2")
    st.write("Please enter your Student ID and Name, then click the 'Next' button.")

    if "user_number" not in st.session_state:
        st.session_state["user_number"] = ""
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = ""

    st.session_state["user_number"] = st.text_input("Student ID", value=st.session_state["user_number"])
    st.session_state["user_name"] = st.text_input("Name", value=st.session_state["user_name"])

    st.write(" ")  # Add space to position the button properly
    if st.button("Next", key="page1_next_button"):
        if st.session_state["user_number"].strip() == "" or st.session_state["user_name"].strip() == "":
            st.error("Please enter both Student ID and Name.")
        else:
            st.session_state["step"] = 2
            st.rerun()

# Page 2: Usage Instructions
def page_2():
    st.title("How to Use the Science Inquiry Assistant")
    st.write(
       """  
        ※ Note: Do not enable browser 'Auto-translate', as it may cause translations to be unnatural or inaccurate. Please disable it if it is active.  

        ① First, share your experimental hypothesis and procedure with the AI assistant. 

        ② The AI will review your hypothesis and procedure and point out strengths and areas for improvement. Feel free to ask any questions you have about this feedback.  

        ③ Once you have asked all your questions, type: "I have asked all my questions."  

        ④ The AI will then ask you some follow-up questions to help you refine your ideas. Think carefully and reply. You may continue to ask questions if you need help.  

        ⑤ After a comprehensive discussion, the AI will inform you when it is okay to click the [Next] button. Click the button only when told to do so!  

        Once you have thoroughly read and understood the instructions above, click [Next] below to proceed.  
        """)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Previous"):
            st.session_state["step"] = 1
            st.rerun()

    with col2:
        if st.button("Next", key="page2_next_button"):
            st.session_state["step"] = 3
            st.rerun()

# Page 3: Chat with GPT
def page_3():
    st.title("Using the Science Inquiry Assistant")
    st.write("Design and refine your inquiry project through conversation with the assistant.")

    # Validate Student ID and Name
    if not st.session_state.get("user_number") or not st.session_state.get("user_name"):
        st.error("Student ID and Name are missing. Please enter them again.")
        st.session_state["step"] = 1
        st.rerun()

    # Initialize conversation state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "user_input_temp" not in st.session_state:
        st.session_state["user_input_temp"] = ""

    if "recent_message" not in st.session_state:
        st.session_state["recent_message"] = {"user": "", "assistant": ""}

    # Chat UI
    user_input = st.text_area(
        "You: ",
        value=st.session_state["user_input_temp"],
        key="user_input",
        on_change=lambda: st.session_state.update({"user_input_temp": st.session_state["user_input"]}),
    )

    if st.button("Send") and user_input.strip():
        # Fetch GPT response
        assistant_response = get_chatgpt_response(user_input)

        # Store recent conversation
        st.session_state["recent_message"] = {"user": user_input, "assistant": assistant_response}

        # Clear input field and reload
        st.session_state["user_input_temp"] = ""
        st.rerun()

    # Display recent conversation
    st.subheader("📌 Recent Message")
    if st.session_state["recent_message"]["user"] or st.session_state["recent_message"]["assistant"]:
        st.write(f"**You:** {st.session_state['recent_message']['user']}")
        st.write(f"**Science Inquiry Assistant:** {st.session_state['recent_message']['assistant']}")
    else:
        st.write("No recent messages yet.")

    # Display conversation history
    st.subheader("📜 Chat History")
    if st.session_state["messages"]:
        for message in st.session_state["messages"]:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**Science Inquiry Assistant:** {message['content']}")
    else:
        st.write("No chat history available.")

    col1, col2 = st.columns([1, 1])

    # Previous button
    with col1:
        if st.button("Previous"):
            st.session_state["step"] = 2
            st.rerun()

    # Next button
    with col2:
        if st.button("Next", key="page3_next_button"):
            st.session_state["step"] = 4
            st.session_state["feedback_saved"] = False  # Reset feedback flag
            st.rerun()

# Save feedback to MySQL database
def save_feedback_to_db(feedback):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # Validate student ID and name
        st.error("Please enter both Student ID and Name.")
        return False  # Failed to save

    try:
        db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
            charset="utf8mb4",
            autocommit=True
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO feedback (number, name, feedback, time)
        VALUES (%s, %s, %s, %s)
        """
        val = (number, name, feedback, now)

        # Execute SQL
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        st.success("Feedback has been successfully saved.")
        return True  # Saved successfully
    except pymysql.MySQLError as db_err:
        st.error(f"Database error occurred: {db_err}")
        return False  # Failed to save
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return False  # Failed to save

# Page 4: Experimental Plan & Summary
def page_4():
    st.title("Assistant's Suggestions")
    st.write("The assistant is organizing your discussion. Please wait a moment...")

    # Generate feedback when navigating to page 4
    if not st.session_state.get("feedback_saved", False):
        # Create inquiry plan based on chat history
        chat_history = "\n".join(f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"])
        prompt = f"The following is the conversation log between the student and the Science Inquiry Assistant:\n{chat_history}\n\n"
        prompt += "Check if the assistant explicitly stated that the student is permitted to click the [Next] button. If this permission was not granted, output: 'You need to click the [Previous] button and continue the discussion with the Science Inquiry Assistant.' Since users often miss whether the permission was actually given, check the chat history rigorously. If permission to click [Next] is present in the chat log, create inquiry content and feedback based on the conversation including: 1. Conversation Summary (Summarize what modifications were agreed upon for the experiment without omitting any key points. Use line breaks for readability). 2. Feedback on the student's inquiry competence. 3. Expected Results (Present the anticipated results in a table considering scientific theories and experimental error, assuming the procedure is carried out as designed. Do not include detailed explanations of the results, just provide the expected outcomes)."

        # Call OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        st.session_state["experiment_plan"] = response.choices[0].message.content

    # Display feedback
    st.subheader("📋 Generated Feedback")
    st.write(st.session_state["experiment_plan"])

    # Combine chat history and feedback
    if "all_data" not in st.session_state:
        st.session_state["all_data"] = []

    all_data_to_store = st.session_state["messages"] + [{"role": "assistant", "content": st.session_state["experiment_plan"]}]

    # Prevent duplicate saves
    if "feedback_saved" not in st.session_state:
        st.session_state["feedback_saved"] = False

    if not st.session_state["feedback_saved"]:
        # Save to MySQL
        if save_to_db(all_data_to_store):
            st.session_state["feedback_saved"] = True
        else:
            st.error("Failed to save data. Please try again.")

    # Previous button (reset feedback state when returning to page 3)
    if st.button("Previous", key="page4_back_button"):
        st.session_state["step"] = 3
        if "experiment_plan" in st.session_state:
            del st.session_state["experiment_plan"]
        st.session_state["feedback_saved"] = False
        st.rerun()

# Main routing logic
if "step" not in st.session_state:
    st.session_state["step"] = 1

if st.session_state["step"] == 1:
    page_1()
elif st.session_state["step"] == 2:
    page_2()
elif st.session_state["step"] == 3:
    page_3()
elif st.session_state["step"] == 4:
    page_4()