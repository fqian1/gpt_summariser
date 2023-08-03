import openai
import json
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi

def get_video_id(url):
    """Extracts the video ID from a YouTube url."""
    video_id = re.search(r'(?<=v=)[^&#]+', url)
    video_id = (video_id.group(0) if video_id else None)

    if video_id is None:
        video_id = re.search(r'(?<=be/)[^&#]+', url)
        video_id = (video_id.group(0) if video_id else None)

    return video_id

def get_transcript(url):
    """Fetches the transcript from a YouTube video and writes it to a text file."""
    video_id = get_video_id(url)
    if video_id is None:
        print("Unable to extract video ID. Please make sure you're passing a valid YouTube URL.")
        return

    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    with open(f'{video_id}_transcript.txt', 'w', encoding='utf-8') as f:
        for item in transcript:
            f.write(item['text'] + ' ')

def chunkify(txt_file, target_chunk_size, overlap):
    with open(txt_file, 'r') as f:
        text = f.read()
    words = text.split()
    total_words = len(words)
    num_chunks = round((total_words - overlap) / (target_chunk_size - overlap))

    # Adjust chunk size to make chunks as equal as possible
    chunk_size = (total_words - (num_chunks - 1) * overlap) // num_chunks
    remainder = (total_words - (num_chunks - 1) * overlap) % num_chunks

    chunks = []
    index = 0
    for _ in range(num_chunks):
        end_index = index + chunk_size + (1 if remainder > 0 else 0)
        chunks.append(' '.join(words[index:end_index]))
        index = end_index - overlap
        remainder -= 1

    return chunks

openai.api_key=os.getenv('OPENAI_API_KEY')

if __name__ == "__main__":
    
    url = input("Enter YouTube video url: ")
    get_transcript(url)

    topic = input("Enter the Topic of the YouTube video: ")

    sys_message = "Summarise these excerpts of a transcript. Make it concise and relevant to the topic: " + str(topic) + ". Exclude information irrelevant to topic."

    conversation = [
        {"role": "system", "content": str(sys_message)},
        {"role": "user", "content": "Summary so far: "}
    ]

    chunks = chunkify(str(get_video_id(url)) + '_transcript.txt', 500, 10)
    final_summary = ""

    for chunk in chunks:
        conversation.append({"role": "user", "content": chunk})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = conversation
        )

        assistant_message = response['choices'][0]['message']['content']
        conversation[1]['content'] = conversation[1]['content'] + assistant_message + " "
        conversation.pop()

        summary_length = conversation[1]['content'].split()
        if len(summary_length) > 2000:
            final_summary = final_summary + conversation[1]['content']
            conversation = [
                {"role": "system", "content": str(sys_message)},
                {"role": "user", "content": "Summary so far: "}
                ]           
            
    final_summary = final_summary + conversation[1]['content']
    print(final_summary)

    with open(str(get_video_id(url)) + '_summary.txt', 'w') as f:
        f.write(final_summary)
        f.close()

