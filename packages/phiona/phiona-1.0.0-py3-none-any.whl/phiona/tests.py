import time
import datetime as dt
from core import (
    get_refresh_token,
    get_new_access_token,
    get_file_status,
    generate_playlist_raw,
    generate_playlist_from_songs,
    generate_playlist_presets,
    get_similar_songs,
    add_new_file,
    edit_song,
    edit_user_playlist,
    delete_song,
    delete_user_playlist,
    delete_generated_playlist,
    create_new_playlist,
    add_song_to_playlist,
    load_user_playlist_songs,
    load_generated_playlists,
    load_generated_playlist_songs,
    load_user_playlists,
    get_artists,
    get_similar_artists,
    multi_target_playlist_creation,
    get_account_tokens,
    save_user_preset,
    duplicate_user_playlist,
    load_session_tags,
    load_unique_session_tags_for_breakdown,
    load_user_sessions_page,
    add_new_performance_metric,
    update_metric_values,
    add_new_session,
    add_a_new_session_tag,
    edit_session,
    delete_session,
    delete_metric_from_session,
    load_sessions_by_tag_combination
)
import json

# generate access and refresh token
username = 'testaccount11'
password = '3d56VM_YGLYl'
# refresh token lasts for 1 week
refresh_token = get_refresh_token(username, password)
# print(refresh_token)
# access token lasts for 4 hours
access_token = get_new_access_token(refresh_token)
# print('access')
# print(access_token)

# # # feed the access token to the api call

# # track_id = add_new_file(access_token, r"C:\Users\Carl\Downloads\drive-download-20250603T085118Z-1-001\Beautiful Day - U2.mp3", 'u2', 'test', '', '', '')
# # print(f"Process song time: {process_time:.2f} seconds")


# # Test get_file_status with new parameters (search, order_by)
# start_time = time.time()
# file_result = get_file_status(access_token, page_n=1)
# print(f"Files page 1: {len(file_result.get('song_info', []))} songs, {file_result.get('n_pages', 0)} pages")
# if file_result.get('song_info'):
#     print(f"First song: {file_result['song_info'][0]['song_title']}")

# # Test with search
# file_result_search = get_file_status(access_token, page_n=1, search='pop')
# print(f"Search 'pop': {len(file_result_search.get('song_info', []))} songs found")

# # Test with emotion search
# file_result_emotion = get_file_status(access_token, page_n=1, search='happy;calm')
# print(f"Search 'happy;calm': {len(file_result_emotion.get('song_info', []))} songs found")

# # Test with order_by
# file_result_ordered = get_file_status(access_token, page_n=1, order_by='-tempo')
# print(f"Ordered by -tempo: {len(file_result_ordered.get('song_info', []))} songs")
# status_time = time.time() - start_time
# print(f"Get file status time: {status_time:.2f} seconds")

# # # get the file status but sorted
# # start_time = time.time()
# # song_info = get_file_status(access_token, page_n=2, sorting_mechanism=['-friendship_love', 'frustration'])
# # status_time = time.time() - start_time
# # print(f"Get file status time: {status_time:.2f} seconds")


# # # generate a playlist 
# # # single hybrid
# # targets1 = [
# #     {
# #         'genre': 'Dance Pop',
# #         'target_circumplex': [0.5, 0.3],
# #         'target_fingerprint': [0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89],
# #         'weighting': '100', 
# #         'avg_date': '2018-12-12',
# #     },
# # ]
# # # multi hybrid
# # targets2 = [
# #     {
# #         'genre': 'Dance Pop',
# #         'target_circumplex': [0.5, 0.3],
# #         'target_fingerprint': [0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89],
# #         'weighting': '60', 
# #         'avg_date': '2018-12-12',
# #     },
# #     {
# #         'genre': 'House',
# #         'target_circumplex': [0.5, 0.3],
# #         'target_fingerprint': [0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89],
# #         'weighting': '40', 
# #         'avg_date': '2022-12-12',
# #     },
# # ]

# # start_time = time.time()
# # playlist_info = generate_playlist_raw(access_token, targets1)
# # status_time = time.time() - start_time
# # print(f"Get playlist status time: {status_time:.2f} seconds")

# # start_time = time.time()
# # playlist_info2 = generate_playlist_presets(access_token, 'fitness-pop')
# # status_time = time.time() - start_time
# # print(f"Get playlist status time: {status_time:.2f} seconds")

# # song_ids = [53, 54, 55, 56, 57]

# # start_time = time.time()
# # playlist_info = generate_playlist_from_songs(access_token, song_ids)
# # status_time = time.time() - start_time
# # print(f"Get playlist status time: {status_time:.2f} seconds")


# # song_ids = [56]

# # start_time = time.time()
# # playlist_info = generate_playlist_from_songs(access_token, song_ids)
# # status_time = time.time() - start_time
# # print(f"Get playlist status time: {status_time:.2f} seconds")


# song_id = 56

# # Test get_similar_songs with new parameters (genre, page)
# start_time = time.time()
# similar_songs_result = get_similar_songs(access_token, song_id)
# print(f"Similar songs: {len(similar_songs_result.get('similar_songs', []))} songs")
# print(f"Available genres: {similar_songs_result.get('available_genres', [])[:5]}...")
# print(f"Page info: page {similar_songs_result.get('page', 1)}/{similar_songs_result.get('total_pages', 1)}")

# # Test with genre filter
# similar_songs_genre = get_similar_songs(access_token, song_id, genre='Pop')
# print(f"Similar songs (Pop genre): {len(similar_songs_genre.get('similar_songs', []))} songs")

# # Test with pagination
# similar_songs_page2 = get_similar_songs(access_token, song_id, page=2)
# print(f"Similar songs page 2: {len(similar_songs_page2.get('similar_songs', []))} songs")
# status_time = time.time() - start_time
# print(f"Get similar songs time: {status_time:.2f} seconds")

# # Test load_user_playlists with new parameters (page_n, search)
# out = load_user_playlists(access_token)
# print(f"User playlists: {len(out.get('playlists_info', []))} playlists, {out.get('n_pages', 0)} pages")

# playlist_id = out['playlists_info'][0]['id'] if out.get('playlists_info') else None
# import random
# import string

# # Test load_user_playlists with search
# playlists_search = load_user_playlists(access_token, search='test')
# print(f"User playlists search 'test': {len(playlists_search.get('playlists_info', []))} playlists")

# # Create and test playlist operations
# random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
# out = create_new_playlist(access_token, random_name)
# print(f"Created playlist: {random_name}")

# if playlist_id:
#     random_name2 = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
#     out = edit_user_playlist(access_token, playlist_id, random_name2)
#     print(f"Edited playlist {playlist_id} to: {random_name2}")
    
#     out = add_song_to_playlist(access_token, playlist_id, song_id)
#     print(f"Added song {song_id} to playlist")
    
#     out = load_user_playlist_songs(access_token, playlist_id)
#     print(f"Playlist songs: {len(out)} songs")
    
#     # Test duplicate_user_playlist (new API)
#     duplicate_result = duplicate_user_playlist(access_token, playlist_id)
#     if duplicate_result.get('error'):
#         print(f"Duplicate error: {duplicate_result['error']}")
#     else:
#         print(f"Duplicated playlist, now have {len(duplicate_result.get('playlist_info', []))} playlists")
    
#     out = delete_user_playlist(access_token, playlist_id)
#     print(f"Deleted playlist {playlist_id}")

# # out = delete_song(access_token, song_id)

# # Test load_generated_playlists with new parameters (page_n, search)
# generated_playlists = load_generated_playlists(access_token)
# print(f"Generated playlists: {len(generated_playlists.get('generated_playlists_info', []))} playlists, {generated_playlists.get('n_pages', 0)} pages")

# # Test with search
# generated_playlists_search = load_generated_playlists(access_token, search='fitness')
# print(f"Generated playlists search 'fitness': {len(generated_playlists_search.get('generated_playlists_info', []))} playlists")

# if generated_playlists.get('generated_playlists_info'):
#     gen_playlist_id = generated_playlists['generated_playlists_info'][0]['id']
#     out = load_generated_playlist_songs(access_token, gen_playlist_id)
#     print(f"Generated playlist songs: {len(out)} songs")
#     # out = delete_generated_playlist(access_token, gen_playlist_id)

# # Test get_artists with new parameters (search, order_by)
# artists_result = get_artists(access_token, page_n=1)
# print(f"Artists: {len(artists_result.get('artist_info', []))} artists, {artists_result.get('n_pages', 0)} pages")

# # Test with search
# artists_search = get_artists(access_token, search='pop')
# print(f"Artists search 'pop': {len(artists_search.get('artist_info', []))} artists")

# # Test with emotion search
# artists_emotion = get_artists(access_token, search='happy;excited')
# print(f"Artists search 'happy;excited': {len(artists_emotion.get('artist_info', []))} artists")

# if artists_result.get('artist_info'):
#     artist_id = artists_result['artist_info'][0]['id']
    
#     # Test get_similar_artists with new parameters (genre, page)
#     similar_artists = get_similar_artists(access_token, artist_id)
#     print(f"Similar artists: {len(similar_artists.get('similar_artists', []))} artists")
#     print(f"Page info: page {similar_artists.get('page', 1)}/{similar_artists.get('total_pages', 1)}")
    
#     # Test with pagination
#     similar_artists_page2 = get_similar_artists(access_token, artist_id, page=2)
#     print(f"Similar artists page 2: {len(similar_artists_page2.get('similar_artists', []))} artists")

# # multi_targets = []

# # multi_targets.append(
# #     {
# #         'targets':[
# #             {
# #                 'genre': 'Electro Pop',
# #                 'target_circumplex': [0.5, 0.3],
# #                 'target_fingerprint': [0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89],
# #                 'weighting': '100', 
# #                 'avg_date': '2010-01-01',
# #             }
# #         ],
# #         'duration': 1800,
# #     }
# # )
# # multi_targets.append(
# #     {
# #         'targets': [
# #             {
# #                 'genre': 'House',
# #                 'target_circumplex': [0.5, 0.3],
# #                 'target_fingerprint': [0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12, 0.89],
# #                 'weighting': '100', 
# #                 'avg_date': '2022-12-12',
# #             },
# #         ],
# #         'duration': 1800,
# #     }
# # )
# # multi_targets.append(
# #     {
# #         'targets': 'fitness-pop',
# #         'duration': 1800,
# #     }
# # )


# # out = multi_target_playlist_creation(access_token, multi_targets)

# # Test get_account_tokens (new API)
# print("\n=== Testing new APIs ===")
# tokens = get_account_tokens(access_token)
# print(f"Account tokens - Signature: {tokens.get('signature_tokens', 0)}, Generation: {tokens.get('generation_tokens', 0)}")

# # Test save_user_preset (new API)
# random_preset_name = 'test_preset_' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
# target_circumplex = [0.5, 0.3]
# target_fingerprint = [0.23, 0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 
#                       0.45, 0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 
#                       0.67, 0.12, 0.89, 0.34, 0.56, 0.78, 0.91, 0.23, 0.45, 0.67, 0.12]
# preset_result = save_user_preset(
#     access_token,
#     preset_name=random_preset_name,
#     description='Test preset from API',
#     avg_date='2020-01-01',
#     genre='Pop',
#     target_circumplex=target_circumplex,
#     target_fingerprint=target_fingerprint,
#     time_length=30
# )
# if preset_result.get('error'):
#     print(f"Save preset error: {preset_result['error']}")
# else:
#     print(f"Saved preset: {random_preset_name}")

# print("\n=== All tests completed ===")

# import ipdb; ipdb.set_trace()


#################################### ANALYTICS ####################################


# # LOAD SESSION TAGS

# tags_result = load_session_tags(access_token)
    
# # Print summary
# tags_list = tags_result.get('session_tags', [])
# print(f"Available session tags: {len(tags_list)} tags")
# print()

# # Print full response in a readable format
# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(tags_result, indent=2))
# print()



# # LOAD UNIQUE SESSION TAGS FOR BREAKDOWN

# tags_result = load_unique_session_tags_for_breakdown(access_token)

# # Print summary
# tags_list = tags_result.get('unique_tags', [])
# print(f"Unique tags used in sessions: {len(tags_list)} tags")
# print()

# # Print full response
# print("=" * 60)
# print("FULL RESPONSE:")
# print("=" * 60)
# print(json.dumps(tags_result, indent=2))
# print()



# # LOAD USER SESSIONS PAGE

# page_number = 1
# sessions_result = load_user_sessions_page(access_token, page_number)
    
# # Print summary
# sessions_list = sessions_result.get('sessions_info', [])
# total_pages = sessions_result.get('n_pages', 1)

# print("=" * 60)
# print("SESSIONS PAGE SUMMARY:")
# print("=" * 60)
# print(f"Page: {page_number} of {total_pages}")
# print(f"Sessions on this page: {len(sessions_list)}")
# print()

# print("=" * 60)
# print("SESSIONS PAGE SUMMARY:")
# print("=" * 60)
# print(f"Page: {page_number} of {total_pages}")
# print(f"Sessions on this page: {len(sessions_list)}")
# print()

# # Print summary table
# print("=" * 60)
# print("SESSIONS SUMMARY TABLE:")
# print("=" * 60)
# print(f"{'ID':<8} {'Name':<30} {'Tags':<20} {'Metrics':<10} {'Playlist'}")
# print("-" * 60)
# for session in sessions_list:
#     tags_str = ', '.join(session.get('tag_names', []))[:18]
#     metrics_count = len(session.get('metric_names', []))
#     # playlist = session.get('playlist_name', 'None')[:15]
#     playlist_name = session.get('playlist_name') or 'None'
#     playlist = playlist_name[:15] if playlist_name else 'None'
#     print(f"{session.get('id'):<8} {session.get('session_name', '')[:28]:<30} {tags_str:<20} {metrics_count:<10} {playlist}")

# # Print first session in detail (if any)
# if sessions_list:
#     print()
#     print("=" * 60)
#     print("FIRST SESSION DETAILS:")
#     print("=" * 60)
#     first_session = sessions_list[0]
#     print(f"ID: {first_session.get('id')}")
#     print(f"Name: {first_session.get('session_name')}")
#     print(f"Description: {first_session.get('session_description', 'N/A')}")
#     print(f"Date Added: {first_session.get('date_added')}")
#     print(f"Length: {first_session.get('sessions_length')}")
#     print(f"Tags: {', '.join(first_session.get('tag_names', []))}")
#     print(f"Metrics: {len(first_session.get('metric_names', []))} metrics")
#     print(f"Playlist: {first_session.get('playlist_name', 'None')} ({first_session.get('playlist_type', 'None')})")
#     print(f"Has Emotion Correlations: {bool(first_session.get('emotion_correlations'))}")
#     print(f"Has Song Impact Scores: {bool(first_session.get('song_impact_scores'))}")



# # ADD NEW PERFORMANCE METRIC

# session_id = 116  # Replace with an actual session ID you own

# # Example metric data
# metric_name = "Test metrics"
# metric_description = "aefqwrqwr"
# metric_type = "continuous"
# metric_time_values = [0, 15, 30, 45, 60, 75, 90]  # Time in seconds
# metric_value_values = [72, 75, 78, 80, 82, 85, 88]  # Heart rate values

# result = add_new_performance_metric(
#     access_token,
#     metric_name,
#     metric_description,
#     metric_type,
#     metric_time_values,
#     metric_value_values,
#     session_id
# )

# # Print full response
# print()
# print("=" * 60)
# print("FULL RESPONSE:")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # UPDATE METRIC VALUES

# metric_id = 734

# # New metric values (different from the original)
# # Original: [0, 15, 30, 45, 60, 75, 90] with values [72, 75, 78, 80, 82, 85, 88]
# metric_time_values = [0, 15, 30, 45, 60, 75, 90, 105, 120]  # Extended time range
# metric_value_values = [70, 73, 76, 79, 81, 84, 87, 89, 91]  # Updated values

# result = update_metric_values(
#     access_token,
#     metric_id,
#     metric_time_values,
#     metric_value_values
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # ADD NEW SESSION

# # Example session data
# session_name = "Test Session from SDK"
# session_description = "Testing add_new_session endpoint"
# session_length = 1800  # 30 minutes
# session_playlist_type = "user"  # or "generated"
# session_playlist_id = 119

# # Example metric data
# session_metrics = [
#     {
#         'metric_name': 'SDK rate',
#         'metric_description': 'testing new session with sdk',
#         'metric_type': 'continuous',
#         'metric_time_values': [0, 15, 30, 45, 60, 75, 90],
#         'metric_value_values': [72, 75, 78, 80, 82, 85, 88]
#     }
# ]

# # Test the function
# result = add_new_session(
#     access_token,
#     session_name,
#     session_description,
#     session_metrics=session_metrics,
#     session_length=session_length,
#     session_playlist_type=session_playlist_type,
#     session_playlist_id=session_playlist_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # ADD NEW SESSION TAG

# # Example tag data
# tag_name = "Yoga"
# tag_description = "Yoga sessions"
# tag_category = "activity"

# # Test the function
# result = add_a_new_session_tag(
#     access_token,
#     tag_name,
#     tag_description,
#     tag_category
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))


# # EDIT SESSION

# # Session to update
# session_id = 118  # Replace with your session ID

# # Updated session data
# session_name = "Updated Test Session from SDK"
# session_description = "Updated description"
# selected_tags = [96]  # Replace with actual tag IDs
# session_playlist_type = "user"
# session_playlist_id = 119

# # Test the function
# result = edit_session(
#     access_token,
#     session_id,
#     session_name,
#     session_description=session_description,
#     selected_tags=selected_tags,
#     session_playlist_type = session_playlist_type,
#     session_playlist_id = session_playlist_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # DELETE SESSION 

# # Session ID to delete
# session_id = 118  # Replace with your session ID

# # Test the function
# result = delete_session(
#     access_token,
#     session_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # DELETE METRIC FROM SESSION

# # Session and metric IDs
# session_id = 118  # Replace with your session ID
# metric_id = 96  # Replace with your metric ID

# # Test the function
# result = delete_metric_from_session(
#     access_token,
#     session_id,
#     metric_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))


# # LOAD SESSION TAGS BY COMBINATION

# # Tag IDs to filter by (sessions must have ALL of these tags)
# tag_ids = [96]  # Replace with your tag IDs

# # Test the function
# result = load_sessions_by_tag_combination(
#     access_token,
#     tag_ids
# )

# # Summary
# print("=" * 60)
# print("SUMMARY:")
# print("=" * 60)
# session_data = result.get('session_data', [])
# print(f"Number of sessions found: {len(session_data)}")
# print(f"\nAverage Emotion Correlations:")

# print(f"\nSession Summary (first 5 sessions):")
# for i, session in enumerate(session_data[:5], 1):
#     print(f"  {i}. {session.get('session_name', 'N/A')} (ID: {session.get('id')})")
#     print(f"     Tags: {', '.join(session.get('tag_names', []))}")
#     print(f"     Metrics: {len(session.get('metric_names', []))} metric(s)")

# if len(session_data) > 5:
#     print(f"  ... and {len(session_data) - 5} more sessions")














###### DEMO ######


# LOAD USER SESSIONS PAGE

# page_number = 1
# sessions_result = load_user_sessions_page(access_token, page_number)

# # Print summary
# sessions_list = sessions_result.get('sessions_info', [])

# # Print summary table
# print("=" * 60)
# print("SESSIONS SUMMARY TABLE:")
# print("=" * 60)
# print(f"{'ID':<8} {'Name':<30} {'Tags':<20} {'Metrics':<10} {'Playlist'}")
# print("-" * 60)
# for session in sessions_list:
#     tags_str = ', '.join(session.get('tag_names', []))[:18]
#     metrics_count = len(session.get('metric_names', []))
#     playlist_name = session.get('playlist_name') or 'None'
#     playlist = playlist_name[:15] if playlist_name else 'None'
#     print(f"{session.get('id'):<8} {session.get('session_name', '')[:28]:<30} {tags_str:<20} {metrics_count:<10} {playlist}")

########
# # Print first session in detail (if any)
# if sessions_list:
#     first_session = sessions_list[0]
#     print()
#     print("=" * 60)
#     print("FIRST SESSION RAW JSON DATA:")
#     print("=" * 60)
#     print(json.dumps(first_session, indent=2))
########



# # ADD NEW SESSION

# # Example session data
# session_name = "Test Session with SDK"
# session_description = "Testing add_new_session endpoint"
# session_length = 1800  # 30 minutes
# session_playlist_type = "user"  # or "generated"
# session_playlist_id = 119

# # Example metric data
# session_metrics = [
#     {
#         'metric_name': 'SDK metric',
#         'metric_description': 'testing new session with sdk',
#         'metric_type': 'continuous',
#         'metric_time_values': [0, 15, 30, 45, 60, 75, 90],
#         'metric_value_values': [72, 75, 78, 80, 82, 85, 88]
#     }
# ]

# # Test the function
# result = add_new_session(
#     access_token,
#     session_name,
#     session_description,
#     session_metrics=session_metrics,
#     session_length=session_length,
#     session_playlist_type=session_playlist_type,
#     session_playlist_id=session_playlist_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # EDIT SESSION

# # Session to update
# session_id = 124  # Replace with your session ID

# # Updated session data
# session_name = "Updated Test Session from SDK"
# session_description = "Updated description"
# selected_tags = [96]  # Replace with actual tag IDs
# session_playlist_type = "user"
# session_playlist_id = "119"

# # Test the function
# result = edit_session(
#     access_token,
#     session_id,
#     session_name,
#     session_description=session_description,
#     selected_tags=selected_tags,
#     session_playlist_type = session_playlist_type,
#     session_playlist_id = session_playlist_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# # DELETE SESSION 

# # Session ID to delete
# session_id = 124  # Replace with your session ID

# # Test the function
# result = delete_session(
#     access_token,
#     session_id
# )

# print("=" * 60)
# print("FULL RESPONSE (what the user will see):")
# print("=" * 60)
# print(json.dumps(result, indent=2))



# LOAD SESSION TAGS BY COMBINATION

# Tag IDs to filter by (sessions must have ALL of these tags)
tag_ids = [96]  # Replace with your tag IDs

# Test the function
result = load_sessions_by_tag_combination(
    access_token,
    tag_ids
)

# Summary
print("=" * 60)
print("SUMMARY:")
print("=" * 60)
session_data = result.get('session_data', [])
print(f"Number of sessions found: {len(session_data)}")
print(f"\nAverage Emotion Correlations:")

print(f"\nSession Summary (first 5 sessions):")
for i, session in enumerate(session_data[:5], 1):
    print(f"  {i}. {session.get('session_name', 'N/A')} (ID: {session.get('id')})")
    print(f"     Tags: {', '.join(session.get('tag_names', []))}")
    print(f"     Metrics: {len(session.get('metric_names', []))} metric(s)")

if len(session_data) > 5:
    print(f"  ... and {len(session_data) - 5} more sessions")

