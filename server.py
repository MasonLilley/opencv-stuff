import asyncio
import websockets
import numpy as np
import cv2
import time
import visionProcessing as vp
import pygame

# Pygame init
pygame.init()
window_size = (640, 480)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Received Image")

async def display_image(websocket, queue):
    frame_count = 0
    start_time = time.time()

    while True:
        binary_data = await queue.get()  # Get the latest data from the queue
        np_array = np.frombuffer(binary_data, dtype=np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is not None:
            frame_count += 1
            
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            cv2.putText(image, f"FPS: {frame_count / (time.time() - start_time):.2f}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Image processing in separate file
            image = vp.processImage(image)
            
            #Py game logic?
            # cv2.imshow("Received Image", image)
            cvImg_To_PygameImg(image)
            
            cv2.waitKey(1) 
        else:
            print("Failed to decode image")

        # FPS calculator
        if time.time() - start_time >= 1:
            frame_count = 0
            start_time = time.time()

async def receive_data(websocket, queue):
    while True:
        binary_data = await websocket.recv()
        
        if queue.full():
            await queue.get()  # Discard the oldest frame
        
        await queue.put(binary_data)  # Add the new data to the queue

async def handle_connection(websocket, path):
    queue = asyncio.Queue(maxsize=1)  # Keep only the latest frame
    consumer_task = asyncio.create_task(display_image(websocket, queue))
    producer_task = asyncio.create_task(receive_data(websocket, queue))
    
    await asyncio.gather(consumer_task, producer_task)

def cvImg_To_PygameImg(image):
    screen.fill([0, 0, 0])
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = np.rot90(image)
    image = pygame.surfarray.make_surface(image)
    screen.blit(image, (0, 0))
    pygame.display.update()

async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 6789):
        print("Server started at ws://0.0.0.0:6789")
        await asyncio.Future()

if __name__ == "__main__":
    cv2.namedWindow("Received Image", cv2.WINDOW_NORMAL)
    asyncio.run(main())
