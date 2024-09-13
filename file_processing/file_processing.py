import librosa
import matplotlib.pyplot as plt
import numpy as np


def is_8d(filename, path=""):
    file, sr = librosa.load(path + filename, mono=False, )
    n_fft = 2048
    hop_length = 1024
    spec_mag = abs(librosa.stft(file, n_fft=n_fft, hop_length=hop_length))

    # Convert the spectrogram into dB
    spec_db = librosa.amplitude_to_db(spec_mag)

    # Compute A-weighting values
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    a_weights = librosa.A_weighting(freqs)
    a_weights = np.expand_dims(a_weights, axis=1)

    # Apply the A-weghting to the spectrogram in dB
    spec_dba = spec_db + a_weights

    # Compute the "loudness" value
    loudness = librosa.feature.rms(S=librosa.db_to_amplitude(spec_dba))

    delta = (np.abs(loudness[0][0] - loudness[1][0])).mean(axis=0)
    print(delta)
    plt.plot(loudness[0][0])
    plt.plot(loudness[1][0])
    plt.text(s=f"{delta}", y=0.1, x=0)
    plt.text(s=filename, y=0.08, x=0)
    plt.show()
    # print(stats.kstest(loudness[0][0], loudness[1][0]))
    # print(stats.chi2_contingency(loudness))
    # n = loudness[0][0]
    # y = loudness[1][0]
    # print(stats.chisquare(n, np.sum(n)/np.sum(y) * y))

    return delta > 0.015


# for i in range(5, 25):
#     filename = f"/Users/antonadonin/PycharmProjects/url_validator/Втюрилась/{i}.mp3"
#     print(filename)
#     is_8d(filename)
#     print("==============")

# filename = f"../8d1.mp3"
# print(filename)
# is_8d(filename)
# print("==============")
# filename = f"../yesterday.mp3"
# print(filename)
# is_8d(filename)
# print("==============")
#
x_1, fs1 = librosa.load('../face/slow.mp3')  # And a second version, slightly faster.
x_2, fs2 = librosa.load('../8d1.mp3')

fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)
librosa.display.waveshow(x_1, sr=fs1, ax=ax[0], color="blue")
ax[0].set(title='Slower Version $X_1$')
ax[0].label_outer()
librosa.display.waveshow(x_2, sr=fs2, ax=ax[1], color="orange")
ax[1].set(title='Faster Version $X_2$')
plt.show()

hop_length = 1024

x_1_chroma = librosa.feature.chroma_cqt(y=x_1, sr=fs1,
                                         hop_length=hop_length)
x_2_chroma = librosa.feature.chroma_cqt(y=x_2, sr=fs2,
                                         hop_length=hop_length)

fig, ax = plt.subplots(nrows=2, sharey=True)
img = librosa.display.specshow(x_1_chroma, x_axis='time',
                               y_axis='chroma',
                               hop_length=hop_length, ax=ax[0], color="blue")
ax[0].set(title='Chroma Representation of $X_1$')
librosa.display.specshow(x_2_chroma, x_axis='time',
                         y_axis='chroma',
                         hop_length=hop_length, ax=ax[1], color="orange")
ax[1].set(title='Chroma Representation of $X_2$')
fig.colorbar(img, ax=ax)

plt.show()


D, wp = librosa.sequence.dtw(X=x_1_chroma, Y=x_2_chroma, metric='cosine')
wp_s = librosa.frames_to_time(wp, sr=fs1, hop_length=hop_length)

fig, ax = plt.subplots()
img = librosa.display.specshow(D, x_axis='time', y_axis='time', sr=fs2,
                               cmap='gray_r', hop_length=hop_length, ax=ax)
ax.plot(wp_s[:, 1], wp_s[:, 0], marker='o', color='r')
ax.set(title='Warping Path on Acc. Cost Matrix $D$',
       xlabel='Time $(X_2)$', ylabel='Time $(X_1)$')
fig.colorbar(img, ax=ax)
plt.show()


from matplotlib.patches import ConnectionPatch

fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, sharey=True, figsize=(8,4))

# Plot x_2
librosa.display.waveshow(x_2, sr=fs1, ax=ax2, color="blue")
ax2.set(title='Faster Version $X_2$')

# Plot x_1
librosa.display.waveshow(x_1, sr=fs2, ax=ax1, color="orange")
ax1.set(title='Slower Version $X_1$')
ax1.label_outer()


n_arrows = 50
for tp1, tp2 in wp_s[::len(wp_s)//n_arrows]:
    # Create a connection patch between the aligned time points
    # in each subplot
    con = ConnectionPatch(xyA=(tp1, 0), xyB=(tp2, 0),
                          axesA=ax1, axesB=ax2,
                          coordsA='data', coordsB='data',
                          color='r', linestyle='--',
                          alpha=0.5)
    con.set_in_layout(False)  # This is needed to preserve layout
    ax2.add_artist(con)

plt.show()