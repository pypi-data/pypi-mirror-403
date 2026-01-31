from golpo import Golpo
import time 

golpo_client = Golpo(api_key='Z0UEHAdA3P8z5edMMjcVs4UBGZhJc6009CQc80XO')

start_time = time.time()
new_script = """
Imagine if creating complex videos was as simple as having a conversation. No timelines, no confusing software, no hours spent dragging and dropping clips. That’s exactly what Golpo AI makes possible. Golpo is an AI-powered video generation platform that turns your ideas into professional explainer videos in minutes. Here’s how it works: You start by describing your concept in plain language—just like you would to a colleague. The AI instantly understands your topic, breaking it down into a clear narrative structure with a strong introduction, key points, and a compelling conclusion. Then, it automatically generates storyboards, visuals, animations, and voice narration that perfectly match your script. Every scene is crafted to visually explain your idea—whether it’s a product demo, a scientific concept, or a startup pitch. You can customize everything: choose a visual style, add your brand colors and logo, and pick from over fifty languages and voice styles. While the AI handles the heavy lifting—timing, transitions, and pacing—you stay in control, editing any frame or line if you want. Behind the scenes, advanced machine learning models align visuals and narration with millisecond precision, ensuring your message is crystal clear. What used to take days of editing can now be done in under ten minutes. Whether you’re a teacher creating a lesson, a startup founder pitching an idea, or a marketer launching a new product, Golpo helps you communicate your ideas visually—fast, beautifully, and at scale. This isn’t just video editing made easier; it’s video creation reimagined. With Golpo, your words become videos.
"""
podcast_url, podcast_script = golpo_client.create_podcast(
    prompt='explain this in detail. make it an explainer',
    uploads=['https://cran.r-project.org/web/packages/aws.s3/aws.s3.pdf'],
)
end_time = time.time()
print(f'time elapsed {end_time - start_time}')
print("******")
print(podcast_url)
print("********")
print(podcast_script)
print("**********")

