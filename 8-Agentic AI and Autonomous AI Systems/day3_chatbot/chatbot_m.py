import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

#create a LLM

llm=ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)

st.title("Level1 : Basic Chatbot")
st.write("Describe your IT problem you are facing and AI will assit you to solve it.")

# chat history - memory
if "messages" not in st.session_state:
    st.session_state.messages=[]

#display previous conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input=st.text_input(
    "Describe your IT issue: "
)

if st.button("Ask"):
    if not user_input:
        st.warning("Please write your IT problem first for me to help you")
    else:
        with st.chat_message("user"):
            st.markdown(user_input)
        
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        #build conversation
        conversation_history=""

        for message in st.session_state.messages:
            conversation_history+=(
                "{message['role']: message['content']}\n"
            )



        prompt=f"""
        you are a helpful IT helpdesk assistant
        you help the user with simple, practical, and concise answer to the IT Problem the user is facing.
        If the issue is not IT related politely apologies and explain that you only help with IT issues
        conversation history :
        {conversation_history}

        if the User issue: {user_input} is IT related you guide with resolution. 
        Rules:
        -Give simple practical answer
        -remember the previous messages in this session before responsding.
        -avoid asking same infromation again.       
        """

        try:
            response=llm.invoke(prompt)
            st.subheader("Helpdesk Response: ")
            st.write({conversation_history})

            ai_response=""
            for item in response.content:
                if isinstance(item,dict) and "text" in item:
                    ai_response+= item["text"]
                
            with st.chat_message("assistant"):
                st.markdown(ai_response)

            #save the ai response
            st.session_state.messages.append(
                {"role":"assistant", "content":ai_response}
            )

        except Exception as e:
            st.error(f"error : {e}")