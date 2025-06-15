package com.example.magicpix;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.provider.Settings;
import android.util.Log;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "MainActivity"; // For logging
    private static final int PERMISSION_REQUEST_CODE = 100; // Unique request code for permissions

    private ImageView imageView;
    private Bitmap selectedImage;
    private Bitmap regeneratedImage; // Store the regenerated image
    private byte[] audioData;

    // ActivityResultLauncher for image selection
    private final ActivityResultLauncher<Intent> imagePickerLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    Uri imageUri = result.getData().getData();
                    if (imageUri != null) {
                        try (InputStream inputStream = getContentResolver().openInputStream(imageUri)) {
                            selectedImage = BitmapFactory.decodeStream(inputStream);
                            imageView.setImageBitmap(selectedImage);
                        } catch (IOException e) {
                            Log.e(TAG, "Error loading image: " + e.getMessage(), e);
                            Toast.makeText(this, R.string.error_loading_image, Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        Toast.makeText(this, R.string.invalid_image_uri, Toast.LENGTH_SHORT).show();
                    }
                }
            }
    );

    // ActivityResultLauncher for audio file selection
    private final ActivityResultLauncher<Intent> audioPickerLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    Uri audioUri = result.getData().getData();
                    if (audioUri != null) {
                        try (InputStream inputStream = getContentResolver().openInputStream(audioUri)) {
                            audioData = new byte[inputStream.available()];
                            inputStream.read(audioData);
                            regeneratedImage = regenerateImageFromAudio(audioData);
                            imageView.setImageBitmap(regeneratedImage);
                            Toast.makeText(this, R.string.image_regenerated_toast, Toast.LENGTH_SHORT).show();
                        } catch (IOException e) {
                            Log.e(TAG, "Error reading audio file: " + e.getMessage(), e);
                            Toast.makeText(this, R.string.error_reading_audio, Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        Toast.makeText(this, R.string.invalid_audio_uri, Toast.LENGTH_SHORT).show();
                    }
                }
            }
    );

    // ActivityResultLauncher for saving audio file
    private final ActivityResultLauncher<Intent> saveAudioLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    Uri fileUri = result.getData().getData();
                    if (fileUri != null && audioData != null) {
                        try (OutputStream outputStream = getContentResolver().openOutputStream(fileUri)) {
                            outputStream.write(audioData);
                            Toast.makeText(this, "Audio saved to: " + fileUri.toString(), Toast.LENGTH_SHORT).show();
                        } catch (IOException e) {
                            Log.e(TAG, "Error saving audio: " + e.getMessage(), e);
                            Toast.makeText(this, R.string.error_saving_audio, Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        Toast.makeText(this, R.string.no_audio_data_toast, Toast.LENGTH_SHORT).show();
                    }
                }
            }
    );

    // ActivityResultLauncher for saving image file
    private final ActivityResultLauncher<Intent> saveImageLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    Uri fileUri = result.getData().getData();
                    if (fileUri != null && regeneratedImage != null) {
                        try (OutputStream outputStream = getContentResolver().openOutputStream(fileUri)) {
                            regeneratedImage.compress(Bitmap.CompressFormat.PNG, 100, outputStream);
                            Toast.makeText(this, "Image saved to: " + fileUri.toString(), Toast.LENGTH_SHORT).show();
                        } catch (IOException e) {
                            Log.e(TAG, "Error saving image: " + e.getMessage(), e);
                            Toast.makeText(this, R.string.error_saving_image, Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        Toast.makeText(this, R.string.regenerate_image_first_toast, Toast.LENGTH_SHORT).show();
                    }
                }
            }
    );

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        imageView = findViewById(R.id.imageView);
        Button selectImageButton = findViewById(R.id.selectImageButton);
        Button convertToAudioButton = findViewById(R.id.convertToAudioButton);
        Button regenerateImageButton = findViewById(R.id.regenerateImageButton);
        Button saveAudioButton = findViewById(R.id.saveAudioButton);
        Button saveImageButton = findViewById(R.id.saveImageButton);

        // Select Image
        selectImageButton.setOnClickListener(v -> {
            if (checkPermissions()) {
                openImagePicker();
            } else {
                requestPermissions();
            }
        });

        // Convert Image to Audio
        convertToAudioButton.setOnClickListener(v -> {
            if (selectedImage != null) {
                audioData = convertImageToAudio(selectedImage);
                Toast.makeText(this, R.string.image_converted_toast, Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, R.string.select_image_toast, Toast.LENGTH_SHORT).show();
            }
        });

        // Regenerate Image from Audio
        regenerateImageButton.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("audio/*"); // Allow only audio files
            audioPickerLauncher.launch(intent);
        });

        // Save Audio
        saveAudioButton.setOnClickListener(v -> {
            if (audioData != null) {
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("audio/wav"); // Set MIME type for audio files
                intent.putExtra(Intent.EXTRA_TITLE, "output.wav"); // Default file name
                saveAudioLauncher.launch(intent);
            } else {
                Toast.makeText(this, R.string.no_audio_data_toast, Toast.LENGTH_SHORT).show();
            }
        });

        // Save Image
        saveImageButton.setOnClickListener(v -> {
            if (regeneratedImage != null) {
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("image/png"); // Set MIME type for image files
                intent.putExtra(Intent.EXTRA_TITLE, "output"); // Default file name
                saveImageLauncher.launch(intent);
            } else {
                Toast.makeText(this, R.string.regenerate_image_first_toast, Toast.LENGTH_SHORT).show();
            }
        });

        Button helpButton = findViewById(R.id.aboutButton);
        helpButton.setOnClickListener(v -> {
            Intent intent = new Intent(MainActivity.this, InstructionsActivity.class);
            startActivity(intent);
        });
    }

    // Check if permissions are granted
    private boolean checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            // Android 14+ requires READ_MEDIA_VISUAL_USER_SELECTED for selected photos access
            return ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED) == PackageManager.PERMISSION_GRANTED;
        } else if (Build.VERSION.SDK_INT == Build.VERSION_CODES.TIRAMISU) {
            // Android 13+ requires READ_MEDIA_IMAGES for accessing images
            return ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_IMAGES) == PackageManager.PERMISSION_GRANTED;
        } else {
            // For older versions, use READ_EXTERNAL_STORAGE
            return ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED;
        }
    }

    // Request permissions
    private void requestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            // Request READ_MEDIA_VISUAL_USER_SELECTED for Android 14+
            ActivityCompat.requestPermissions(
                    this,
                    new String[]{Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED},
                    PERMISSION_REQUEST_CODE
            );
        } else if (Build.VERSION.SDK_INT == Build.VERSION_CODES.TIRAMISU) {
            // Request READ_MEDIA_IMAGES for Android 13+
            ActivityCompat.requestPermissions(
                    this,
                    new String[]{Manifest.permission.READ_MEDIA_IMAGES},
                    PERMISSION_REQUEST_CODE
            );
        } else {
            // Request READ_EXTERNAL_STORAGE for older versions
            ActivityCompat.requestPermissions(
                    this,
                    new String[]{Manifest.permission.READ_EXTERNAL_STORAGE},
                    PERMISSION_REQUEST_CODE
            );
        }
    }

    // Handle permission request results
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // Permission granted, proceed with image selection
                openImagePicker();
            } else {
                // Permission denied, show a message to the user
                Toast.makeText(this, "Allow the Permissions. Cannot access images.", Toast.LENGTH_SHORT).show();
                // Open app settings to allow the user to grant permission manually
                openAppSettings();
            }
        }
    }

    // Open app settings
    private void openAppSettings() {
        Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
        Uri uri = Uri.fromParts("package", getPackageName(), null);
        intent.setData(uri);
        startActivity(intent);
    }

    // Open image picker
    private void openImagePicker() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        imagePickerLauncher.launch(intent);
    }

    // Convert image to audio
    private byte[] convertImageToAudio(Bitmap image) {
        int width = image.getWidth();
        int height = image.getHeight();
        byte[] pixelData = new byte[width * height * 3]; // 3 bytes per pixel (RGB)

        // Populate pixelData with RGB values
        int pixelIndex = 0;
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int pixel = image.getPixel(x, y);
                int red = (pixel >> 16) & 0xFF;
                int green = (pixel >> 8) & 0xFF;
                int blue = pixel & 0xFF;

                pixelData[pixelIndex++] = (byte) red;
                pixelData[pixelIndex++] = (byte) green;
                pixelData[pixelIndex++] = (byte) blue;
            }
        }

        // Create WAV header
        int sampleRate = 44100; // Standard sample rate
        int numChannels = 1; // Mono audio
        int bitDepth = 8; // 8-bit audio
        byte[] wavHeader = createWavHeader(pixelData.length, sampleRate, numChannels, bitDepth);

        // Store width and height as the first 8 bytes after the header
        byte[] dimensionData = new byte[8];
        dimensionData[0] = (byte) (width >> 24);
        dimensionData[1] = (byte) (width >> 16);
        dimensionData[2] = (byte) (width >> 8);
        dimensionData[3] = (byte) (width);
        dimensionData[4] = (byte) (height >> 24);
        dimensionData[5] = (byte) (height >> 16);
        dimensionData[6] = (byte) (height >> 8);
        dimensionData[7] = (byte) (height);

        // Combine WAV header, dimension data, and pixel data
        byte[] wavData = new byte[wavHeader.length + dimensionData.length + pixelData.length];
        System.arraycopy(wavHeader, 0, wavData, 0, wavHeader.length);
        System.arraycopy(dimensionData, 0, wavData, wavHeader.length, dimensionData.length);
        System.arraycopy(pixelData, 0, wavData, wavHeader.length + dimensionData.length, pixelData.length);

        return wavData;
    }

    // Create WAV header
    private byte[] createWavHeader(int audioDataLength, int sampleRate, int numChannels, int bitDepth) {
        int byteRate = sampleRate * numChannels * bitDepth / 8;
        int blockAlign = numChannels * bitDepth / 8;
        int totalDataLen = audioDataLength + 36; // 36 is the size of the header minus the first 8 bytes

        byte[] header = new byte[44];
        // RIFF chunk
        header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
        header[4] = (byte) (totalDataLen & 0xff);
        header[5] = (byte) ((totalDataLen >> 8) & 0xff);
        header[6] = (byte) ((totalDataLen >> 16) & 0xff);
        header[7] = (byte) ((totalDataLen >> 24) & 0xff);
        header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
        // fmt subchunk
        header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
        header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0; // Subchunk size (16 for PCM)
        header[20] = 1; header[21] = 0; // Audio format (1 for PCM)
        header[22] = (byte) numChannels; header[23] = 0; // Number of channels
        header[24] = (byte) (sampleRate & 0xff);
        header[25] = (byte) ((sampleRate >> 8) & 0xff);
        header[26] = (byte) ((sampleRate >> 16) & 0xff);
        header[27] = (byte) ((sampleRate >> 24) & 0xff);
        header[28] = (byte) (byteRate & 0xff);
        header[29] = (byte) ((byteRate >> 8) & 0xff);
        header[30] = (byte) ((byteRate >> 16) & 0xff);
        header[31] = (byte) ((byteRate >> 24) & 0xff);
        header[32] = (byte) blockAlign; header[33] = 0; // Block align
        header[34] = (byte) bitDepth; header[35] = 0; // Bits per sample
        // data subchunk
        header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
        header[40] = (byte) (audioDataLength & 0xff);
        header[41] = (byte) ((audioDataLength >> 8) & 0xff);
        header[42] = (byte) ((audioDataLength >> 16) & 0xff);
        header[43] = (byte) ((audioDataLength >> 24) & 0xff);

        return header;
    }

    // Regenerate image from audio
    private Bitmap regenerateImageFromAudio(byte[] audioData) {
        // Skip the WAV header (first 44 bytes)
        int headerSize = 44;
        if (audioData.length <= headerSize) {
            Toast.makeText(this, "Invalid audio data for image regeneration.", Toast.LENGTH_SHORT).show();
            return null;
        }

        // Extract width and height from the first 8 bytes after the header
        int width = ((audioData[headerSize] & 0xFF) << 24) |
                ((audioData[headerSize + 1] & 0xFF) << 16) |
                ((audioData[headerSize + 2] & 0xFF) << 8) |
                (audioData[headerSize + 3] & 0xFF);

        int height = ((audioData[headerSize + 4] & 0xFF) << 24) |
                ((audioData[headerSize + 5] & 0xFF) << 16) |
                ((audioData[headerSize + 6] & 0xFF) << 8) |
                (audioData[headerSize + 7] & 0xFF);

        // Create a new bitmap with the extracted dimensions
        Bitmap regeneratedImage = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);

        // Decode the pixel data (skip the first 8 bytes after the header)
        int pixelIndex = headerSize + 8; // Start reading pixel data after the header and dimensions
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int red = audioData[pixelIndex++] & 0xFF;
                int green = audioData[pixelIndex++] & 0xFF;
                int blue = audioData[pixelIndex++] & 0xFF;
                int pixel = (0xFF << 24) | (red << 16) | (green << 8) | blue;
                regeneratedImage.setPixel(x, y, pixel);
            }
        }

        return regeneratedImage;
    }
}