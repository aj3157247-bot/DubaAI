#include "whisper.h"

#include <cstring>
#include <string>

extern "C" {

struct DubaAIWhisperContext {
    whisper_context *ctx;
};

DubaAIWhisperContext* dubaai_whisper_init(
    const char *model_path
) {
    if (!model_path) {
        return nullptr;
    }

    whisper_context_params params =
        whisper_context_default_params();

    whisper_context *ctx =
        whisper_init_from_file_with_params(
            model_path,
            params
        );

    if (!ctx) {
        return nullptr;
    }

    DubaAIWhisperContext *result =
        new DubaAIWhisperContext;

    result->ctx = ctx;

    return result;
}


int dubaai_whisper_transcribe(
    DubaAIWhisperContext *wrapper,
    const float *samples,
    int sample_count,
    const char *language
) {
    if (!wrapper || !wrapper->ctx) {
        return -1;
    }

    if (!samples || sample_count <= 0) {
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
        language ? language : "en";

    params.n_threads = 4;

    int result =
        whisper_full(
            wrapper->ctx,
            params,
            samples,
            sample_count
        );

    return result;
}


int dubaai_whisper_segment_count(
    DubaAIWhisperContext *wrapper
) {
    if (!wrapper || !wrapper->ctx) {
        return -1;
    }

    return whisper_full_n_segments(
        wrapper->ctx
    );
}


const char* dubaai_whisper_segment_text(
    DubaAIWhisperContext *wrapper,
    int index
) {
    if (!wrapper || !wrapper->ctx) {
        return nullptr;
    }

    if (
        index < 0 ||
        index >= whisper_full_n_segments(
            wrapper->ctx
        )
    ) {
        return nullptr;
    }

    return whisper_full_get_segment_text(
        wrapper->ctx,
        index
    );
}


void dubaai_whisper_free(
    DubaAIWhisperContext *wrapper
) {
    if (!wrapper) {
        return;
    }

    if (wrapper->ctx) {
        whisper_free(
            wrapper->ctx
        );
    }

    delete wrapper;
}

}
