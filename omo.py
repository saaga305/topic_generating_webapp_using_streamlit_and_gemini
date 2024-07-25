#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 11 17:05:06 2024

@author: me
"""

import streamlit as st
import os
import json
import google.generativeai as genai


def configure_genai():
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        st.error("Google API key is not set in the environment variables.")
        st.stop()
    genai.configure(api_key=api_key)


def get_question(topic):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Generate a 100-level STEM question on the topic '{topic}'. Provide the response in the following JSON format:
    {{
        "question": "Your question here?",
        "choices": ["option1", "option2", "option3", "option4"],
        "correct_answer": "correct_option",
        "explanation": "Explanation of the correct answer."
    }}
    """
    generation_config = genai.types.GenerationConfig(temperature=0.5)
    try:
        response = model.generate_content(prompt, generation_config=generation_config)
        st.write("Raw response from API:", response.text)  # Print the raw response for debugging
        data = json.loads(response.text.strip("```json").strip("```").strip())  # Handle API response format
        if not all(k in data for k in ("question", "choices", "correct_answer", "explanation")):
            raise ValueError("Incomplete response from API")
    except json.JSONDecodeError as e:
        st.error(f"JSON decode error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.stop()
    return data


def initialize_session_state():
    session_state = st.session_state
    session_state.form_count = 0
    session_state.quiz_data = None
    session_state.current_topic = ""
    session_state.user_tired = False
    session_state.show_next_question_button = False


def main():
    configure_genai()

    st.title('Smart Bowen Quiz App')

    if 'form_count' not in st.session_state:
        initialize_session_state()

    if st.session_state.user_tired:
        st.write("You have chosen to quit the quiz. Thank you for participating!")
        return

    topic = st.text_input("Enter the topic for the quiz:", st.session_state.current_topic)

    if topic and topic != st.session_state.current_topic:
        st.session_state.current_topic = topic
        with st.spinner("Generating question..."):
            st.session_state.quiz_data = get_question(topic)
        st.session_state.form_count += 1
        st.session_state.show_next_question_button = False

    if st.session_state.quiz_data:
        quiz_data = st.session_state.quiz_data
        st.markdown(f"**Question:** {quiz_data['question']}")

        form = st.form(key=f"quiz_form_{st.session_state.form_count}")
        user_choice = form.radio("Choose an answer:", quiz_data['choices'])
        submitted = form.form_submit_button("Submit your answer")

        if submitted:
            if user_choice == quiz_data['correct_answer']:
                st.success("Correct! Click 'Next Question' to continue.")
                st.session_state.show_next_question_button = True
            else:
                st.error("Incorrect. Try again.")
                st.markdown(f"**Explanation:** {quiz_data['explanation']}")
                st.session_state.show_next_question_button = False

    if 'show_next_question_button' in st.session_state and st.session_state.show_next_question_button:
        if st.button("Next Question"):
            with st.spinner("Generating next question..."):
                st.session_state.quiz_data = get_question(st.session_state.current_topic)
            st.session_state.form_count += 1
            st.session_state.show_next_question_button = False
            st.experimental_rerun()  # Force a rerun to update the UI

    if st.button("Quit"):
        st.session_state.user_tired = True
        st.write("You have chosen to quit the quiz. Thank you for participating!")


if __name__ == '__main__':
    main()
