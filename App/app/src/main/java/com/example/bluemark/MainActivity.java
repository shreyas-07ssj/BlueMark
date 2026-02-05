package com.example.bluemark;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseData;
import android.bluetooth.le.AdvertiseSettings;
import android.bluetooth.le.BluetoothLeAdvertiser;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.ParcelUuid;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.nio.charset.StandardCharsets;
import java.util.UUID;

public class MainActivity extends AppCompatActivity {

    private BluetoothLeAdvertiser advertiser;
    private Button btnBroadcast;
    private TextView txtStatus;

    // MUST MATCH PYTHON SCRIPT EXACTLY
    private static final String CLASS_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b";

    // Your Student Identity (Generated Once)
    private String myStudentId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        btnBroadcast = findViewById(R.id.btnBroadcast);
        txtStatus = findViewById(R.id.txtStatus);

        // 1. Generate or Load Identity
        myStudentId = getPersistentIdentity();
        txtStatus.setText("My ID: " + myStudentId + "\n(Ready to Broadcast)");

        // Initialize Bluetooth
        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter != null) {
            advertiser = adapter.getBluetoothLeAdvertiser();
        }

        btnBroadcast.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startBroadcasting();
            }
        });
    }

    private void startBroadcasting() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) {
                return; // Permissions handled in onCreate usually
            }
        }

        if (advertiser == null) return;

        AdvertiseSettings settings = new AdvertiseSettings.Builder()
                .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
                .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
                .setConnectable(false)
                .build();

        ParcelUuid pUuid = new ParcelUuid(UUID.fromString(CLASS_UUID));
        String shortID = myStudentId.substring(0, 4);

        AdvertiseData data = new AdvertiseData.Builder()
                .setIncludeDeviceName(false) // Keep this FALSE
                // .addServiceUuid(pUuid)    <-- REMOVE THIS LINE (It wastes 18 bytes)

                // Keep ONLY this line. It contains the UUID + The ID
                .addServiceData(pUuid, shortID.getBytes(StandardCharsets.UTF_8))
                .build();

        Log.d("BlueMesh", "Starting broadcast...");
        advertiser.startAdvertising(settings, data, advertisingCallback);
    }

    // Helper: Generates a random ID once and saves it
    private String getPersistentIdentity() {
        SharedPreferences prefs = getSharedPreferences("BlueMeshPrefs", MODE_PRIVATE);
        String id = prefs.getString("STUDENT_ID", null);

        if (id == null) {
            id = UUID.randomUUID().toString();
            prefs.edit().putString("STUDENT_ID", id).apply();
        }
        return id;
    }

    private final AdvertiseCallback advertisingCallback = new AdvertiseCallback() {
        @Override
        public void onStartSuccess(AdvertiseSettings settingsInEffect) {
            super.onStartSuccess(settingsInEffect);
            runOnUiThread(() -> {
                String shortID = myStudentId.substring(0, 4);
                txtStatus.setText("Status: BROADCASTING ✅\nID Sent: " + shortID);
                txtStatus.setTextColor(getResources().getColor(android.R.color.holo_green_dark));
                btnBroadcast.setEnabled(false);
            });
        }

        @Override
        public void onStartFailure(int errorCode) {
            super.onStartFailure(errorCode);
            runOnUiThread(() -> {
                txtStatus.setText("Status: FAILED ❌ (Error " + errorCode + ")");
                txtStatus.setTextColor(getResources().getColor(android.R.color.holo_red_dark));
            });
        }
    };
}