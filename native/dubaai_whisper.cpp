#include "whisper.h"

#include <cstdlib>

extern "C" {

struct DubaAIWhisperContext {
    whisper_context* ctx;
};

/*
 * Create Whisper context from a GGML model.
 */
DubaAIWhisperContext* dubaai_whisper_init(
    const char* model_path
) {
    if (model_path == nullptr) {
        return nullptr;
    }

    whisper_context_params params =
        whisper_context_default_params();

    whisper_context* ctx =
        whisper_init_from_file_with_params(
            model_path,
            params
        );

    if (ctx == nullptr) {
        return nullptr;
    }

    DubaAIWhisperContext* wrapper =
        static_cast<DubaAIWhisperContext*>(
            std::malloc(sizeof(DubaAIWhisperContext))
        );

    if (wrapper == nullptr) {
        whisper_free(ctx);
        return nullptr;
    }

    wrapper->ctx = ctx;

    return wrapper;
}


/*
 * Run Whisper transcription.
 *
 * samples:
 *   16 kHz mono float32 PCM
 */
int dubaai_whisper_transcribe(
    DubaAIWhisperContext* wrapper,
    const float* samples,
    int sample_count,
    const char* language
) {
    if (wrapper == nullptr || wrapper->ctx == nullptr) {
        return -1;
    }

    if (samples == nullptr || sample_count <= 0) {
        return -2;
    }

    whisper_full_params params =
        whisper_full_default_params(
            WHISPER_SAMPLING_GREEDY
        );

    params.print_progress = false;
    params.print_realtime = false;
    params.print_timestamps = false;
    params.print_special = false;

    params.translate = false;

    params.language =
        (language != nullptr && language[0] != '\0')
            ? language
            : "en";

    /*
     * Android ARM64:
     * Keep the number of threads moderate so the
     * application does not consume excessive memory.
     */
    params.n_threads = 4;

    /*
     * Do not generate timestamps in the first
     * implementation. The Python layer receives
     * the recognized segments from Whisper.
     */
    params.no_timestamps = true;

    return whisper_full(
        wrapper->ctx,
        params,
        samples,
        sample_count
    );
}


/*
 * Return number of recognized segments.
 */
int dubaai_whisper_segment_count(
    DubaAIWhisperContext* wrapper
) {
    if (wrapper == nullptr || wrapper->ctx == nullptr) {
        return -1;
    }

    return whisper_full_n_segments(
        wrapper->ctx
    );
}


/*
 * Return text for one recognized segment.
 */
const char* dubaai_whisper_segment_text(
    DubaAIWhisperContext* wrapper,
    int index
) {
    if (wrapper == nullptr || wrapper->ctx == nullptr) {
        return nullptr;
    }

    int count =
        whisper_full_n_segments(
            wrapper->ctx
        );

    if (index < 0 || index >= count) {
        return nullptr;
    }

    return whisper_full_get_segment_text(
        wrapper->ctx,
        index
    );
}


/*
 * Free Whisper context.
 */
void dubaai_whisper_free(
    DubaAIWhisperContext* wrapper
) {
    if (wrapper == nullptr) {
        return;
    }

    if (wrapper->ctx != nullptr) {
        whisper_free(
            wrapper->ctx
        );

        wrapper->ctx = nullptr;
    }

    std::free(wrapper);
}

}
