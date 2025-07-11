import streamlit as st
import numpy as np
import pickle
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
from gtts import gTTS

# Load VGG16 model
vgg_model = VGG16()
vgg_model = Model(inputs=vgg_model.inputs, outputs=vgg_model.layers[-2].output)

# Load the trained image captioning model
model = load_model('model.h5')

# Load the tokenizer
with open('tokenizer.pkl', 'rb') as tokenizer_file:
    tokenizer = pickle.load(tokenizer_file)
    
# Set custom web page title
st.set_page_config(page_title="Caption Generator App", page_icon="📷")

# Streamlit app
st.title("Image Caption Generator")
st.markdown(
    "Upload an image, and this app will generate a caption for it using a trained LSTM model."
)

# Upload image
uploaded_image = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

# Process uploaded image
if uploaded_image is not None:
    # Display loading spinner while processing
    with st.spinner("Generating caption..."):
        # Load image
        image = load_img(uploaded_image, target_size=(224, 224))
        image = img_to_array(image)
        image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))
        image = preprocess_input(image)

        # Extract features using VGG16
        image_features = vgg_model.predict(image, verbose=0)

        # Max caption length
        max_caption_length = 35
        
        # Define function to get word from index
        def get_word_from_index(index, tokenizer):
            return next(
                (word for word, idx in tokenizer.word_index.items() if idx == index), None
            )

        # Generate caption using the model
        def predict_caption(model, image_features, tokenizer, max_caption_length):
            caption = "startseq"
            for _ in range(max_caption_length):
                sequence = tokenizer.texts_to_sequences([caption])[0]
                sequence = pad_sequences([sequence], maxlen=max_caption_length)
                yhat = model.predict([image_features, sequence], verbose=0)
                predicted_index = np.argmax(yhat)
                predicted_word = get_word_from_index(predicted_index, tokenizer)
                caption += " " + predicted_word
                if predicted_word is None or predicted_word == "endseq":
                    break
            return caption

        # Generate caption
        generated_caption = predict_caption(model, image_features, tokenizer, max_caption_length)

        # Remove startseq and endseq
        generated_caption = generated_caption.replace("startseq", "").replace("endseq", "")

        st.subheader(generated_caption)

    # Step 1: Generate the audio for the caption using gTTS
        tts = gTTS(generated_caption, lang='en')
        audio_path = "predicted_caption.mp3"
        tts.save(audio_path)

    # Step 2: Display the audio player before the image
        st.audio(audio_path, format='audio/mp3')
        st.markdown("Generated Caption")
        st.subheader("Uploaded Image")
        uploaded_image.seek(0)
        st.image(uploaded_image)
